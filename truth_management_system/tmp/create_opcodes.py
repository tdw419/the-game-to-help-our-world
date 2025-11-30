from default_api import default_api

# Opcode for GENERATE_PRISMA_SCHEMA
default_api.create_Opcode(
    name="GENERATE_PRISMA_SCHEMA",
    description="Generates a Prisma schema.prisma file for a PostgreSQL database based on a provided data model definition.",
    input_schema={
        "type": "object",
        "properties": {
            "orm_choice": {"type": "string", "enum": ["Prisma"]},
            "data_model_definition": {
                "type": "string",
                "description": "Textual definition of the data model (e.g., entity names, fields, types, relationships). A simple format like 'ModelName { fieldName: FieldType; }' is expected."
            },
            "additional_options": {
                "type": "object",
                "description": "Additional Prisma-specific options, e.g., for custom types or indexes."
            }
        },
        "required": ["orm_choice", "data_model_definition"]
    },
    output_schema={
        "type": "object",
        "properties": {
            "schema_prisma_content": {"type": "string", "description": "The generated content for the schema.prisma file."},
            "suggested_next_steps": {"type": "string", "description": "Instructions for the user to set up and use the generated Prisma schema."}
        },
        "required": ["schema_prisma_content", "suggested_next_steps"]
    },
    confidence=0.95
)

# Opcode for GENERATE_TYPEORM_SCHEMA
default_api.create_Opcode(
    name="GENERATE_TYPEORM_SCHEMA",
    description="Generates TypeORM entity files and an ormconfig.json for a PostgreSQL database based on a provided data model definition.",
    input_schema={
        "type": "object",
        "properties": {
            "orm_choice": {"type": "string", "enum": ["TypeORM"]},
            "data_model_definition": {
                "type": "string",
                "description": "Textual definition of the data model (e.g., entity names, fields, types, relationships). A simple format like 'ModelName { fieldName: FieldType; }' is expected."
            },
            "additional_options": {
                "type": "object",
                "description": "Additional TypeORM-specific options, e.g., for custom decorators or column types."
            }
        },
        "required": ["orm_choice", "data_model_definition"]
    },
    output_schema={
        "type": "object",
        "properties": {
            "entity_files_content": {
                "type": "object",
                "patternProperties": {
                    "^[a-zA-Z0-9_]+\\.ts$": {"type": "string"}
                },
                "description": "A dictionary where keys are entity filenames (e.g., 'User.ts') and values are their TypeScript content."
            },
            "ormconfig_content": {"type": "string", "description": "The generated content for the ormconfig.json file."},
            "suggested_next_steps": {"type": "string", "description": "Instructions for the user to set up and use the generated TypeORM entities."}
        },
        "required": ["entity_files_content", "ormconfig_content", "suggested_next_steps"]
    },
    confidence=0.95
)

# Opcode for EXECUTE_DB_NEXT_STEPS
default_api.create_Opcode(
    name="EXECUTE_DB_NEXT_STEPS",
    description="Executes a series of suggested database setup or migration steps, simulating shell commands or scripts.",
    input_schema={
        "type": "object",
        "properties": {
            "steps_to_execute": {
                "type": "string",
                "description": "A textual description of the steps to be executed (e.g., '1. npm install; 2. prisma db push')."
            },
            "context_info": {
                "type": "object",
                "description": "Additional context about the execution environment or ORM, if needed."
            }
        },
        "required": ["steps_to_execute"]
    },
    output_schema={
        "type": "object",
        "properties": {
            "execution_log": {"type": "string", "description": "Detailed log of the simulated execution process."},
            "success_status": {"type": "boolean", "description": "True if all steps simulated successfully, false otherwise."}
        },
        "required": ["execution_log", "success_status"]
    },
    confidence=0.90
)
