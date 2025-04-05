from psycopg2 import sql, extras
import pandas as pd
import uuid
import numpy as np
from loggin_config import LogManager
import re

class SyncManager:
    def __init__(self, global_conn, local_conn):
        self.global_conn = global_conn
        self.local_conn = local_conn
        LogManager.logger.info('SyncManager Initialized')

    def execute_sync(self, select_sql, insert_sql, table_name, column_names, ztime=None, zutime=None, having_clause=False, clear_table_first=False):
        print('execute_sync')
        LogManager.logger.info(f"{table_name}, {ztime}, {zutime}")
        
        aliases = re.findall(r'\b(\w+)\.\w+', select_sql)
        aliases = list(dict.fromkeys(aliases))
        
        params = []
    
        if 'GROUP BY' not in select_sql.upper():
            if ztime or zutime:
                conditions = []  # Store all conditions here
                for alias in aliases:
                    condition_parts = []
                    if ztime:
                        condition_parts.append(f"{alias}.ztime > %s")
                        params.append(ztime)
                    if zutime:
                        condition_parts.append(f"{alias}.zutime > %s")
                        params.append(zutime)
                    
                    conditions.append(" OR ".join(condition_parts))
                
                # Adding all the conditions to the SQL query
                condition = " AND ".join(conditions)
                condition = f" AND ({condition})" if 'WHERE' in select_sql else f" WHERE ({condition})"
                select_sql += condition

        elif 'GROUP BY' in select_sql.upper():
            conditions = []
            for alias in aliases:
                parts = []
                if ztime:
                    parts.append(f"{alias}.ztime > %s")
                    params.append(ztime)
                if zutime:
                    parts.append(f"{alias}.zutime > %s")
                    params.append(zutime)
                if parts:  # Check if parts is not empty this also helps if its the first time data is being synced
                    conditions.append(" OR ".join(parts))
            if conditions:
                condition = " OR ".join(conditions)
                select_sql += f" HAVING ({condition})"

        LogManager.logger.info(f"Modified SQL Query: {select_sql}")

        # Fetch records from global_db
        global_cur = self.global_conn.cursor()
        global_cur.execute(select_sql, params)
        updated_records = global_cur.fetchall()
        column_names = [desc[0] for desc in global_cur.description]
        # LogManager.logger.info(column_names)
        global_cur.close()
        
        if not updated_records:
            LogManager.logger.info(f"No new updates in {table_name}.")
            return
        
        # Convert the records to DataFrame and clean timestamp columns
        df = pd.DataFrame(updated_records, columns=column_names)
        timestamp_columns = ['itime', 'utime']  
        for col in timestamp_columns:
            if col in df.columns:
                df[col].replace({pd.NaT: None}, inplace=True)
        
        # Get the maximum existing serial number for the UUID prefix and set the new UUIDs
        prefix = str(uuid.uuid4())[:8]  
        local_cur = self.local_conn.cursor()
        query = f"SELECT MAX(SUBSTRING(uuid FROM 9)::INTEGER) FROM {table_name} WHERE uuid LIKE '{prefix}%'"
        local_cur.execute(query)
        max_serial = local_cur.fetchone()[0] or 0
        df['uuid'] = [f"{prefix}{max_serial + i + 1}" for i in range(len(df))]
        cols = ['uuid'] + [col for col in df if col != 'uuid']
        df = df.reindex(columns=cols)
                # Check if the table needs to be cleared first
        if clear_table_first:
            truncate_sql = f"TRUNCATE TABLE {table_name}"
            local_cur.execute(truncate_sql)
        # Insert the records into local_db
        values = list(df.itertuples(index=False, name=None))
        extras.execute_values(local_cur, insert_sql, values, template=None, page_size=100)
        self.local_conn.commit()
        local_cur.close()
        
        LogManager.logger.info(f"{len(df)} records updated in {table_name}.")
    
    def sync_missing_entries(self, local_table_name, global_table_name, column_names_global, column_names_local, select_sql, insert_sql):
        print('sync_missing_entries',column_names_global,column_names_local)
        assert len(column_names_global) == 2 and len(column_names_local) == 2, "Expected two columns for comparison."

        # Step 1: Fetch all unique pairs of the specified columns from the local database.
        local_cur = self.local_conn.cursor()
        local_cur.execute(f"SELECT DISTINCT {column_names_local[0]}, {column_names_local[1]} FROM {local_table_name}")
        local_pairs = set(tuple(row) for row in local_cur.fetchall())
        local_cur.close()
        print('first_local_cur_complete')

        # Step 2: Fetch all unique pairs of the specified columns from the global database.
        global_cur = self.global_conn.cursor()
        global_cur.execute(f"SELECT DISTINCT {column_names_global[0]}, {column_names_global[1]} FROM {global_table_name}")
        global_pairs = set(tuple(row) for row in global_cur.fetchall())
        global_cur.close()
        print('first_global_cur_complete')
        # Step 3: Identify the pairs that are in the global database but not in the local database.
        missing_pairs = global_pairs - local_pairs
        
        if not missing_pairs:
            LogManager.logger.info(f"No missing pairs in {local_table_name}.")
            print('no_missing_pairs')
            return
        
        # Step 4: Fetch the complete rows for these missing pairs from the global database.
        conditions = " OR ".join([f"({global_table_name}.{column_names_global[0]} = %s AND {global_table_name}.{column_names_global[1]} = %s)" for _ in missing_pairs])
        
       # Check if WHERE already exists in the select_sql and append with AND or WHERE accordingly.
        if "GROUP BY" in select_sql.upper():
            if "HAVING" in select_sql.upper():
                select_sql += f" AND {conditions}"
            else:
                select_sql += f" HAVING {conditions}"
        else:
            if "WHERE" in select_sql.upper():
                select_sql += f" AND {conditions}"
            else:
                select_sql += f" WHERE {conditions}"

        # LogManager.logger.info(f"Modified SQL Query: {select_sql}")
        print('first_global_cur_complete', len(missing_pairs))

        parameters = [item for pair in missing_pairs for item in pair]
        global_cur = self.global_conn.cursor()
        global_cur.execute(select_sql, parameters)
        missing_records = global_cur.fetchall()
        column_names = [desc[0] for desc in global_cur.description]
        # LogManager.logger.info(f"Column names from global cursor: {column_names}")
        global_cur.close()
        print('secong_global_cur_complete')

        # Step 5: Insert these rows into the local database.
        df = pd.DataFrame(missing_records, columns=column_names)
        # LogManager.logger.info(f"Inserting Columns: {df.columns}")
        timestamp_columns = ['itime', 'utime']  
        for col in timestamp_columns:
            if col in df.columns:
                df[col].replace({pd.NaT: None}, inplace=True)

        # Get the maximum existing serial number for the UUID prefix and set the new UUIDs
        prefix = str(uuid.uuid4())[:8]  
        local_cur = self.local_conn.cursor()
        query = f"SELECT MAX(SUBSTRING(uuid FROM 9)::INTEGER) FROM {local_table_name} WHERE uuid LIKE '{prefix}%'"
        local_cur.execute(query)
        max_serial = local_cur.fetchone()[0] or 0
        df['uuid'] = [f"{prefix}{max_serial + i + 1}" for i in range(len(df))]
        cols = ['uuid'] + [col for col in df if col != 'uuid']
        df = df.reindex(columns=cols)

        values = list(df.itertuples(index=False, name=None))
        local_cur = self.local_conn.cursor()
        extras.execute_values(local_cur, insert_sql, values, template=None, page_size=100)
        self.local_conn.commit()
        local_cur.close()

        LogManager.logger.info(f"{len(df)} missing records added to {local_table_name} in local database.")

    def sync_all(self, tables_dict):
            print('sync_all')
            ##glmst
            select_sql_glmst = """
                SELECT 
                    glmst.ztime as itime,
                    glmst.zutime as utime,
                    glmst.zid,
                    glmst.xacc as ac_code,
                    glmst.xdesc as ac_name,
                    glmst.xacctype as ac_type,
                    glmst.xhrc1 as ac_lv1,
                    glmst.xhrc2 as ac_lv2,
                    glmst.xhrc3 as ac_lv3,
                    glmst.xhrc4 as ac_lv4,
                    glmst.xaccusage as usage
                FROM glmst
            """
            insert_sql_glmst = """
                INSERT INTO glmst (
                    uuid, itime, utime, zid, ac_code, ac_name, ac_type,
                    ac_lv1, ac_lv2, ac_lv3, ac_lv4, usage
                ) VALUES %s
            """
            column_names_glmst = ['itime', 'utime', 'zid', 'ac_code', 'ac_name', 'ac_type', 'ac_lv1', 'ac_lv2', 'ac_lv3', 'ac_lv4', 'usage']
            ztime = tables_dict['glmst']['itime']
            zutime = tables_dict['glmst']['utime']
            self.execute_sync(select_sql_glmst, insert_sql_glmst, 'glmst', column_names_glmst, ztime, zutime)
            self.sync_missing_entries('glmst','glmst',['zid','xacc'],['zid','ac_code'],select_sql_glmst,insert_sql_glmst)


            # For gldetail table
            select_sql_gldetail = """
                SELECT 
                    gldetail.ztime as itime,
                    gldetail.zutime as utime,
                    gldetail.zid,
                    gldetail.xacc as ac_code,
                    gldetail.xsub as ac_sub,
                    gldetail.xproj as project,
                    gldetail.xvoucher as voucher,
                    gldetail.xprime as value
                FROM gldetail
            """
            insert_sql_gldetail = """
                INSERT INTO gldetail (
                    uuid, itime, utime, zid, ac_code, ac_sub, project, voucher, value
                ) VALUES %s
            """
            column_names_gldetail = ['itime', 'utime', 'zid', 'ac_code', 'ac_sub','project','voucher','value']
            ztime = tables_dict['gldetail']['itime']
            zutime = tables_dict['gldetail']['utime']
            self.execute_sync(select_sql_gldetail, insert_sql_gldetail, 'gldetail', column_names_gldetail, ztime, zutime)
            self.sync_missing_entries('gldetail','gldetail',['zid','xvoucher'],['zid','voucher'],select_sql_gldetail,insert_sql_gldetail)

            # For glheader table
            select_sql_glheader = """
                SELECT 
                    glheader.ztime as itime,
                    glheader.zutime as utime,
                    glheader.zid,
                    glheader.xvoucher as voucher,
                    glheader.xdate as date,
                    glheader.xyear as year,
                    glheader.xper as month
                FROM glheader
            """
            insert_sql_glheader = """
                INSERT INTO glheader (
                    uuid, itime, utime, zid, voucher, date, year, month
                ) VALUES %s
            """
            column_names_glheader = ['itime', 'utime', 'zid', 'voucher', 'date', 'year', 'month']
            ztime = tables_dict['glheader']['itime']
            zutime = tables_dict['glheader']['utime']
            self.execute_sync(select_sql_glheader, insert_sql_glheader, 'glheader', column_names_glheader, ztime, zutime)
            self.sync_missing_entries('glheader','glheader',['zid','xvoucher'],['zid','voucher'],select_sql_glheader,insert_sql_glheader)

            # For purchase table
            select_sql_purchase = """
                SELECT 
                    poodt.ztime as itime,
                    poodt.zutime as utime,
                    poord.zid as zid,
                    COALESCE(pogrn.xdate, poord.xdate) AS combinedate,
                    poord.xpornum as povoucher,
                    pogrn.xgrnnum as grnvoucher,
                    poodt.xitem as itemcode,
                    poord.xcounterno as shipmentname,
                    poodt.xqtyord as quantity,
                    poodt.xrate as cost,
                    poord.xstatuspor as status
                FROM poord
                JOIN poodt ON poord.xpornum = poodt.xpornum AND poord.zid = poodt.zid
                LEFT JOIN pogrn ON poord.xpornum = pogrn.xpornum AND poord.zid = pogrn.zid
                WHERE poord.xstatuspor IN ('5-Received','1-Open')
            """
            insert_sql_purchase = """
                INSERT INTO purchase (
                    uuid, itime, utime, zid, combinedate, povoucher, grnvoucher,
                    itemcode, shipmentname, quantity, cost, status
                ) VALUES %s
            """
            column_names_purchase = ['itime', 'utime', 'zid', 'combinedate', 'povoucher', 'grnvoucher',
                                    'itemcode', 'shipmentname', 'quantity', 'cost', 'status']
            ztime = tables_dict['purchase']['itime']
            zutime = tables_dict['purchase']['utime']
            self.execute_sync(select_sql_purchase, insert_sql_purchase, 'purchase', column_names_purchase, ztime, zutime)
            self.sync_missing_entries('purchase','poord',['zid','xpornum'],['zid','povoucher'],select_sql_purchase,insert_sql_purchase)
            # For sales table
            select_sql_sales = """
                SELECT 
                    opddt.ztime as itime,
                    opddt.zutime as utime,
                    opddt.zid as zid,
                    opdor.xdornum as ordernumber, 
                    opdor.xdate as date, 
                    opdor.xsp as sp_id,  
                    opdor.xcus as cusid, 
                    opddt.xitem as itemcode,
                    SUM(opddt.xqty) as quantity,
                    SUM(opddt.xlineamt) as totalsales,
                    SUM(imtrn.xval) as cost
                FROM opdor
                LEFT JOIN opddt ON opdor.xdornum = opddt.xdornum AND opdor.zid = opddt.zid
                LEFT JOIN imtrn ON opdor.xdornum = imtrn.xdocnum AND opddt.xdornum = imtrn.xdocnum AND opddt.xitem = imtrn.xitem AND opddt.zid = imtrn.zid AND opdor.zid = imtrn.zid
                GROUP BY opddt.ztime,opddt.zutime,opdor.ztime,opdor.zutime,imtrn.ztime,imtrn.zutime,opddt.zid,opdor.zid,imtrn.zid,opdor.xdornum,opddt.xdornum,imtrn.xdocnum, opdor.xdate, opdor.xsp, opdor.xcus, opddt.xitem
            """

            insert_sql_sales = """
                INSERT INTO sales (
                    uuid, itime, utime, zid, ordernumber, date, sp_id, cusid, itemcode, quantity, totalsales, cost
                ) VALUES %s
            """

            column_names_sales = ['itime', 'utime', 'zid', 'ordernumber', 'date', 'sp_id', 'cusid', 'itemcode', 'quantity', 'totalsales', 'cost']
            ztime = tables_dict['sales']['itime']
            zutime = tables_dict['sales']['utime']
            self.execute_sync(select_sql_sales, insert_sql_sales, 'sales', column_names_sales, ztime, zutime, having_clause=True)
            self.sync_missing_entries('sales','opdor',['zid','xdornum'],['zid','ordernumber'],select_sql_sales,insert_sql_sales)
            # For return table
            select_sql_return = """
                SELECT 
                    opcdt.ztime as itime,
                    opcdt.zutime as utime,
                    opcdt.zid as zid,
                    opcrn.xcrnnum as revoucher, 
                    opcrn.xdate as date, 
                    opcrn.xcus as cusid, 
                    opcrn.xemp as sp_id,  
                    opcdt.xitem as itemcode, 
                    SUM(opcdt.xqty) as returnqty, 
                    SUM(opcdt.xlineamt) as treturnamt,
                    SUM(imtrn.xval) as returncost
                FROM opcrn
                INNER JOIN opcdt ON opcrn.xcrnnum = opcdt.xcrnnum AND opcrn.zid = opcdt.zid
                INNER JOIN imtrn ON opcrn.xcrnnum = imtrn.xdocnum AND opcdt.xcrnnum = imtrn.xdocnum AND opcdt.xitem = imtrn.xitem AND opcdt.zid = imtrn.zid AND opcrn.zid = imtrn.zid
                GROUP BY opcdt.ztime,opcdt.zutime,opcrn.ztime,opcrn.zutime,imtrn.ztime,imtrn.zutime,opcdt.zid,opcrn.zid,imtrn.zid,opcrn.xcrnnum,opcdt.xcrnnum,imtrn.xdocnum,opcrn.xdate,opcrn.xcus,opcrn.xemp,opcdt.xitem
            """

            insert_sql_return = """
                INSERT INTO return (
                    uuid, itime, utime, zid, revoucher, date, cusid, sp_id, itemcode, returnqty, treturnamt, returncost
                ) VALUES %s
            """

            column_names_return = ['itime', 'utime', 'zid', 'revoucher', 'date', 'cusid', 'sp_id', 'itemcode', 'returnqty', 'treturnamt', 'returncost']
            ztime = tables_dict['return']['itime']
            zutime = tables_dict['return']['utime']
            self.execute_sync(select_sql_return, insert_sql_return, 'return', column_names_return, ztime, zutime, having_clause=True)
            # self.sync_missing_entries('return','opcrn',['zid','xcrnnum'],['zid','revoucher'],select_sql_return,insert_sql_return)
            
            # For stock table
            select_sql_stock = """
                SELECT 
                    imtrn.zid as zid,
                    imtrn.xitem as itemcode,
                    SUM(imtrn.xqty * imtrn.xsign) as stockqty,
                    SUM(imtrn.xval * imtrn.xsign) AS stockvalue
                FROM imtrn
                GROUP BY imtrn.zid,imtrn.xitem
            """

            insert_sql_stock = """
                INSERT INTO stock (
                    uuid, zid, itemcode, stockqty, stockvalue
                ) VALUES %s
            """

            column_names_stock = ['zid', 'itemcode', 'stockqty', 'stockvalue']
            # ztime = tables_dict['stock']['itime']
            # zutime = tables_dict['stock']['utime']
            self.execute_sync(select_sql_stock, insert_sql_stock, 'stock', column_names_stock, ztime=None, zutime=None, having_clause=True, clear_table_first=True)

            # For stock value table
            select_sql_stock_value = """
                SELECT 
                    imtrn.zid as zid,
                    imtrn.xyear as year,
                    imtrn.xper as month,
                    imtrn.xwh as warehouse,
                    SUM(imtrn.xval * imtrn.xsign) as stockvalue 
                FROM imtrn
                GROUP BY imtrn.zid, imtrn.xyear, imtrn.xper, imtrn.xwh
            """

            insert_sql_stock_value = """
                INSERT INTO stock_value (
                    uuid, zid, year, month, warehouse, stockvalue
                ) VALUES %s
            """

            column_names_stock_value = ['zid', 'year', 'month', 'warehouse', 'stockvalue']
            # ztime = tables_dict['stock_value']['itime']
            # zutime = tables_dict['stock_value']['utime']
            self.execute_sync(select_sql_stock_value, insert_sql_stock_value, 'stock_value', column_names_stock_value, ztime=None, zutime=None, having_clause=True, clear_table_first=True)

            # For cacus table
            select_sql_cacus = """
                SELECT 
                    cacus.ztime as itime,
                    cacus.zutime as utime,
                    cacus.zid as zid,
                    cacus.xcus as cusid,
                    cacus.xshort as cusname,
                    cacus.xadd2 as cusadd,
                    cacus.xcity as cuscity,
                    cacus.xstate as cusstate,
                    cacus.xmobile as cusmobile,
                    cacus.xtaxnum as cusmobile2
                FROM cacus
            """

            insert_sql_cacus = """
                INSERT INTO cacus (
                    uuid, itime, utime, zid, cusid, cusname, cusadd, cuscity, cusstate, cusmobile, cusmobile2
                ) VALUES %s
            """

            column_names_cacus = ['itime', 'utime', 'zid', 'cusid', 'cusname', 'cusadd', 'cuscity', 'cusstate', 'cusmobile', 'cusmobile2']
            ztime = tables_dict['cacus']['itime']
            zutime = tables_dict['cacus']['utime']
            self.execute_sync(select_sql_cacus, insert_sql_cacus, 'cacus', column_names_cacus, ztime, zutime)
            self.sync_missing_entries('cacus','cacus',['zid','xcus'],['zid','cusid'],select_sql_cacus,insert_sql_cacus)
            # For caitem table
            select_sql_caitem = """
                SELECT 
                    caitem.ztime as itime,
                    caitem.zutime as utime,
                    caitem.zid as zid,
                    caitem.xitem as itemcode,
                    caitem.xdesc as itemname,
                    caitem.xgitem as itemgroup,
                    caitem.xabc as itemgroup2,
                    caitem.xscode as packcode
                FROM caitem
            """

            insert_sql_caitem = """
                INSERT INTO caitem (
                    uuid, itime, utime, zid, itemcode, itemname, itemgroup, itemgroup2, packcode
                ) VALUES %s
            """

            column_names_caitem = ['itime', 'utime', 'zid', 'itemcode', 'itemname', 'itemgroup', 'itemgroup2', 'packcode']
            ztime = tables_dict['caitem']['itime']
            zutime = tables_dict['caitem']['utime']
            self.execute_sync(select_sql_caitem, insert_sql_caitem, 'caitem', column_names_caitem, ztime, zutime)
            self.sync_missing_entries('caitem','caitem',['zid','xitem'],['zid','itemcode'],select_sql_cacus,insert_sql_cacus)
            # For prmst table
            select_sql_prmst = """
                SELECT 
                    prmst.ztime as itime,
                    prmst.zutime as utime,
                    prmst.zid as zid,
                    prmst.xemp as spid,
                    prmst.xname as spname,
                    prmst.xdept as department,
                    prmst.xdesig as designation
                FROM prmst
            """

            insert_sql_prmst = """
                INSERT INTO employee (
                    uuid, itime, utime, zid, spid, spname, department, designation
                ) VALUES %s
            """

            column_names_prmst = ['itime', 'utime', 'zid', 'spid', 'spname', 'department', 'designation']
            ztime = tables_dict['employee']['itime']
            zutime = tables_dict['employee']['utime']
            self.execute_sync(select_sql_prmst, insert_sql_prmst, 'employee', column_names_prmst, ztime, zutime)
            self.sync_missing_entries('employee','prmst',['zid','xemp'],['zid','spid'],select_sql_cacus,insert_sql_cacus)



