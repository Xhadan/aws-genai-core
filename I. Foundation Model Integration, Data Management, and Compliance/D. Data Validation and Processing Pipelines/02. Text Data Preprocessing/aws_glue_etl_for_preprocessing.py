import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql.functions import udf, col
from pyspark.sql.types import StringType
import re

# Initialize Glue context
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)

# UDF for text cleaning
@udf(returnType=StringType())
def clean_text_udf(text):
    if text is None:
        return ""
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

# Read source data
datasource = glueContext.create_dynamic_frame.from_catalog(
    database="genai_data",
    table_name="raw_documents"
)

# Convert to DataFrame for transformations
df = datasource.toDF()

# Apply preprocessing
df_cleaned = df.withColumn("cleaned_text", clean_text_udf(col("raw_text")))

# Write to destination
output_frame = DynamicFrame.fromDF(df_cleaned, glueContext, "output")
glueContext.write_dynamic_frame.from_options(
    frame=output_frame,
    connection_type="s3",
    connection_options={"path": "s3://bucket/processed/"},
    format="json"
)