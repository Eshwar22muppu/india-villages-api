import pandas as pd
import psycopg2
import os
import glob
from dotenv import load_dotenv

load_dotenv()

def get_conn():
    return psycopg2.connect(os.getenv("DATABASE_URL"))

conn = get_conn()
cur = conn.cursor()
print("Connected!")

cur.execute('INSERT INTO "Country" (name, code) VALUES (\'India\', \'IN\') ON CONFLICT (code) DO NOTHING')
conn.commit()
cur.execute('SELECT id FROM "Country" WHERE code = \'IN\'')
country_id = cur.fetchone()[0]

excel_files = sorted(glob.glob("dataset/*.xls") + glob.glob("dataset/*.xlsx"))
print(f"Found {len(excel_files)} files\n")

state_map = {}
district_map = {}
subdistrict_map = {}

def safe(val):
    if val is None: return ""
    s = str(val).strip()
    if s.endswith(".0"): s = s[:-2]
    return "" if s.lower() == "nan" else s

def reconnect():
    global conn, cur
    try:
        cur.close()
        conn.close()
    except: pass
    conn = get_conn()
    cur = conn.cursor()
    print("  Reconnected!")

for filepath in excel_files:
    fname = os.path.basename(filepath)
    print(f"Processing: {fname}")
    try:
        try:
            df = pd.read_excel(filepath, sheet_name="Village Directory", dtype=str)
        except:
            df = pd.read_excel(filepath, sheet_name=0, dtype=str)

        needed = ["STATE NAME","DISTRICT NAME","Area Name",
                  "MDDS STC","MDDS DTC","MDDS Sub_DT","MDDS PLCN"]
        if not all(c in df.columns for c in needed):
            print(f"  Skipping - wrong columns")
            continue

        df = df.fillna("")
        print(f"  Rows: {len(df)}")

        for _, row in df[["MDDS STC","STATE NAME"]].drop_duplicates().iterrows():
            code = safe(row["MDDS STC"])
            name = safe(row["STATE NAME"])
            if not code or not name or code in state_map:
                continue
            try:
                cur.execute('INSERT INTO "State" (code,name,"countryId") VALUES (%s,%s,%s) ON CONFLICT (code) DO NOTHING',
                           (code, name, country_id))
                conn.commit()
                cur.execute('SELECT id FROM "State" WHERE code=%s', (code,))
                r = cur.fetchone()
                if r: state_map[code] = r[0]
            except Exception as e:
                conn.rollback()

        for _, row in df[["MDDS STC","MDDS DTC","DISTRICT NAME"]].drop_duplicates().iterrows():
            sc   = safe(row["MDDS STC"])
            dc   = safe(row["MDDS DTC"])
            name = safe(row["DISTRICT NAME"])
            key  = f"{sc}_{dc}"
            if not sc or not dc or not name or key in district_map or sc not in state_map:
                continue
            try:
                cur.execute('INSERT INTO "District" (code,name,"stateId") VALUES (%s,%s,%s) ON CONFLICT DO NOTHING',
                           (dc, name, state_map[sc]))
                conn.commit()
                cur.execute('SELECT id FROM "District" WHERE code=%s AND "stateId"=%s',
                           (dc, state_map[sc]))
                r = cur.fetchone()
                if r: district_map[key] = r[0]
            except Exception as e:
                conn.rollback()

        for _, row in df[["MDDS STC","MDDS DTC","MDDS Sub_DT","SUB-DISTRICT NAME"]].drop_duplicates().iterrows():
            sc   = safe(row["MDDS STC"])
            dc   = safe(row["MDDS DTC"])
            sdc  = safe(row["MDDS Sub_DT"])
            name = safe(row["SUB-DISTRICT NAME"])
            dkey = f"{sc}_{dc}"
            skey = f"{sc}_{dc}_{sdc}"
            if not sdc or not name or skey in subdistrict_map or dkey not in district_map:
                continue
            try:
                cur.execute('INSERT INTO "SubDistrict" (code,name,"districtId") VALUES (%s,%s,%s) ON CONFLICT DO NOTHING',
                           (sdc, name, district_map[dkey]))
                conn.commit()
                cur.execute('SELECT id FROM "SubDistrict" WHERE code=%s AND "districtId"=%s',
                           (sdc, district_map[dkey]))
                r = cur.fetchone()
                if r: subdistrict_map[skey] = r[0]
            except Exception as e:
                conn.rollback()

        villages = []
        for _, row in df.iterrows():
            sc   = safe(row["MDDS STC"])
            dc   = safe(row["MDDS DTC"])
            sdc  = safe(row["MDDS Sub_DT"])
            vc   = safe(row["MDDS PLCN"])
            name = safe(row["Area Name"])
            skey = f"{sc}_{dc}_{sdc}"
            if skey not in subdistrict_map or not name:
                continue
            villages.append((vc, name, subdistrict_map[skey]))

        CHUNK = 500
        inserted = 0
        for i in range(0, len(villages), CHUNK):
            chunk = villages[i:i+CHUNK]
            try:
                args = ",".join(cur.mogrify("(%s,%s,%s)", v).decode() for v in chunk)
                cur.execute(f'INSERT INTO "Village" (code,name,"subDistrictId") VALUES {args} ON CONFLICT DO NOTHING')
                conn.commit()
                inserted += len(chunk)
            except Exception as e:
                try:
                    conn.rollback()
                except:
                    reconnect()

        print(f"  Done: {inserted} villages")

    except Exception as e:
        print(f"  ERROR: {e}")
        try:
            conn.rollback()
        except:
            reconnect()
        continue

try:
    print("\n=== FINAL COUNTS ===")
    for table in ["State","District","SubDistrict","Village"]:
        cur.execute(f'SELECT COUNT(*) FROM "{table}"')
        print(f"{table}: {cur.fetchone()[0]}")
    cur.close()
    conn.close()
except:
    pass
print("Import complete!")