import random
import csv
import sqlite3
import json
import pandas as pd
import os
RANDOM_SEED = 56235
random.seed(RANDOM_SEED)

def export(db_path, df, sample=False):
    """
    Load data from a pandas DataFrame into an SQLite database.

    Args:
        db_path (str): Path to the SQLite database file.
        df (pd.DataFrame): DataFrame containing the data.
    """

    df['original_index'] = df.reset_index().index

    text_columns = [
        "query_template",
        "constraints",
        "spec_template",
        "query_type",
        "creation_method",
        "chart_type",
        "chart_complexity",
        "query_base",
        "spec",
        "solution",
        "dataset_schema",
        "query",
        
    ]

    number_columns = [
        "expertise",
        "formality",
    ]

    all_columns = text_columns + number_columns

    # if db_path exists, delete it
    if os.path.exists(db_path):
        os.remove(db_path)

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Define table schema
    columns = ["id INTEGER PRIMARY KEY"] + \
              ["original_id INTEGER"] + \
              ["combined_id TEXT UNIQUE"] + \
              ["template_id INTEGER"] + \
              ["expanded_id INTEGER"] + \
              ["paraphrased_id INTEGER"] + \
              [f"{col} TEXT" for col in text_columns] + \
              [f"{col} REAL" for col in number_columns]

    create_table_query = f"CREATE TABLE data ({', '.join(columns)});"
    cur.execute(create_table_query)

    # Process DataFrame rows
    template_ID = 0
    expanded_ID = 0
    paraphrased_ID = 0
    prev_row = None
    index = 0
    for _, row in df.iterrows():
        if sample:
            # Sample 10% of the data
            if random.random() > 0.1:
                continue
        original_index = row.get('original_index', None)
        row = row.to_dict()  # Convert row to dictionary for easier access
        row['constraints'] = json.dumps(row.get('constraints', None))
        row['solution'] = json.dumps(row.get('solution', None))
        # Print basic loading bar
        if index % 1000 == 0:
            print(f"Loaded {index} rows of {len(df)}", end="\r")

        if index > 0:
            if row["query_template"] != prev_row["query_template"] or row["constraints"] != prev_row["constraints"]:
                template_ID += 1
                expanded_ID = 0
                paraphrased_ID = 0
            elif row["query_base"] != prev_row["query_base"] or row["dataset_schema"] != prev_row["dataset_schema"]:
                expanded_ID += 1
                paraphrased_ID = 0
            else:
                paraphrased_ID += 1

        combined_ID = f"{template_ID}_{expanded_ID}_{paraphrased_ID}"

        values = [index, original_index, combined_ID, template_ID, expanded_ID, paraphrased_ID] + [
            row.get(col, None)
            for col in all_columns
        ]
        prev_row = row
        index += 1
        placeholders = ", ".join(["?"] * len(values))
        execute_command = f"INSERT INTO data (id, original_id, combined_id, template_id, expanded_id, paraphrased_id, {', '.join(all_columns)}) VALUES ({placeholders});"
        cur.execute(execute_command, values)

    # Create index
    index_template_expanded = "CREATE INDEX idx_template_expanded ON data(template_id, expanded_id);"
    cur.execute(index_template_expanded)

    conn.commit()
    conn.close()

db_path = ("/Users/arthe/HMS/DQVis-Generation/database.sqlite")
df = pd.read_csv("/Users/arthe/HMS/DQVis-Generation/basic-expanded-template.csv")
print(df.columns)
export(db_path, df)