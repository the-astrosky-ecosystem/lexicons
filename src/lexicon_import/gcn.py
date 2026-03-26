from lexicon_import import WORKING_DIRECTORY, LEXICON_DIRECTORY
import requests
import urllib.request
import zipfile
import shutil
import json


# Todo some are really nasty and are skipped for now
SKIPPED_SCHEMAS = [
    "icecube",
    "svom",
    "dsa110",
    "einstein_probe",
    "burstcube",
    "heasarc",  # Has bad name
]


def update():
    print("Starting GCN lexicon update.")
    schema_folder = _fetch_schema()
    _clean_schema_tree(schema_folder)
    _convert_all_files(schema_folder)
    _move_gcn_files(schema_folder)

    print(
        "All done! Make sure to do `goat lex lint` and see if the lexicon update is "
        "correct."
    )


def convert_gcn_schema_to_atproto_lexicon(file):
    # Read file
    with open(file) as f:
        schema = json.load(f)

    # Add new keys
    schema["lexicon"] = 1  # Todo need robust versioning!
    schema["$type"] = "com.atproto.lexicon.schema"

    # Rename certain keys
    schema["id"] = "eco.astrosky.transient.gcn." + schema.pop("$id").split("/gcn/")[
        1
    ].replace(".schema.json", "").replace("/", ".")

    # Grab a description for the schema
    description = schema.pop("title", "Untitled record type")
    if "description" in schema:
        description = f"{description}: {schema.pop('description')}"
    schema["description"] = (
        description
        + " N.B. This schema is adapted from a schema provided by the NASA GCN at https://github.com/nasa-gcn/gcn-schema"
    )

    # Start recording any non-main properties (i.e. other defs)
    other_schema_defs = dict()

    # Look for properties
    if "properties" in schema:
        properties: dict[str, dict] = schema.pop("properties")

        if "allOf" in schema:
            properties.update()

    # Alternatively, some schemas just have a single enum (cry)
    elif "enum" in schema:
        properties = dict(value=dict(type="string", enum=schema.pop("enum")))

    # Some schemas only contain refs to others
    elif "allOf" in schema:
        properties = schema.pop("allOf")

    # Otherwise, raise error
    else:
        raise RuntimeError(f"Schema file {file} not supported!")

    # Remove any "schema true" properties
    properties = {k: v for k, v in properties.items() if k != "$schema"}

    # Handle any properties that need converting
    print(file)
    for key, prop in properties.items():
        description = prop.get("description", "")

        # Replace 'oneOf' or 'anyOf' options with string
        # Todo this works because there are only two, both of which are just either floats or length-two float arrays. Improve this, e.g. with a specific new schema for something that's either an array or not!
        if "oneOf" in prop:
            prop = prop["oneOf"][0]  # Todo fix
        if "anyOf" in prop:
            prop = prop["anyOf"][0]  # Todo fix

        # "ref" types handling
        if "$ref" in prop and "type" not in prop:
            prop["type"] = "ref"
            prop["ref"] = prop.pop("$ref").replace(
                ".schema.json", ""
            )  # Todo refs need to not be relative

        # String enums need converting once again
        if "enum" in prop and "type" not in prop:
            prop["type"] = "string"

        # Floating point numbers not allowed in ATProtocol
        string_flag = False
        if prop["type"] == "number":
            prop["type"] = "string"
            string_flag = True
        if prop["type"] == "array":
            if "items" in prop:
                for item in prop["items"]:
                    if item["type"] == "number":
                        item["type"] = "string"
                        string_flag = True

        if string_flag:
            prop["description"] = (
                description
                + " (WARNING: string representation of floating point number)"
            ).strip()

        properties[key] = prop

    # Replace all properties with defs
    schema["defs"] = dict(
        main=dict(
            type="record",
            description=description,
            record=dict(
                type="object",
                # required=?  # Todo: required key
                properties=properties,
            ),
        ),
        **other_schema_defs,
    )

    # Remove out of schema keys we don't need
    bad_keys = ["$schema", "type"]
    for key in bad_keys:
        schema.pop(key, None)

    # Save over file
    with open(file, "w") as f:
        json.dump(schema, f, indent=2)


def _fetch_schema():
    """Fetches the current GCN schema, extracts it, and saves it locally."""
    # First off we need to grab the link to the latest file. bit annoying for this repo
    response = requests.get(
        "https://api.github.com/repos/nasa-gcn/gcn-schema/releases/latest"
    )
    json = response.json()
    download_link = json["zipball_url"]

    # Download the file
    print("Downloading", download_link)
    file_zip = WORKING_DIRECTORY / "gcn-schema.zip"
    urllib.request.urlretrieve(download_link, file_zip)

    # Extract to folder
    file_folder = WORKING_DIRECTORY / "gcn-schema"
    if file_folder.exists():
        shutil.rmtree(file_folder)

    with zipfile.ZipFile(file_zip, "r") as zip_ref:
        zip_ref.extractall(file_folder)

    # Cleanup zip file
    file_zip.unlink()

    # Get the name of the actual fucking repo because it comes as some stupid hash
    gcn_repo = [x.parent for x in file_folder.glob("*/README.md")][0]

    return gcn_repo / "gcn"


def _clean_schema_tree(folder):
    """Removes example schema files and moves files to more sensible names."""
    example_files = folder.glob("**/*example.json")
    for file in example_files:
        file.unlink()

    schema_files = folder.glob("**/*schema.json")
    for file in schema_files:
        shutil.move(file, file.parent / file.name.replace(".schema", ""))


def _convert_all_files(folder):
    files = sorted(list(folder.glob("**/*.json")))
    print(f"Converting {len(files)} files to ATProto Lexicon format")
    for file in files:
        if any([x in str(file) for x in SKIPPED_SCHEMAS]):
            print(f"Skipping {file.parent}/{file.name}!")
            file.unlink()
            continue
        convert_gcn_schema_to_atproto_lexicon(file)


def _move_gcn_files(folder):
    old_folder = LEXICON_DIRECTORY / "transient/gcn"
    if old_folder.exists():
        shutil.rmtree(old_folder)

    (LEXICON_DIRECTORY / "transient").mkdir(exist_ok=True, parents=True)
    shutil.move(folder, LEXICON_DIRECTORY / "transient")
