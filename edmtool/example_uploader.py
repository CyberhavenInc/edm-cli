from edmtool.client import UploaderClient

# Example Usage
client = UploaderClient("http://api.example.com")

# Create a new database
response = client.create_database(
    name="Clients PII",
    description=
    "A DB file containing a unique ID, Name, Last Name, SSN and Address entries of our clients",
    version=1,
    proximity=100,
    size=629834,
    algorithm="spooky")
print(response)

# Upload to the database
if response:
    db_id = response.get("id")
    if db_id:
        response = client.upload_database(db_id, "path_to_your_file.csv")
        print(response)
