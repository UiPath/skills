#!/usr/bin/env node
/**
 * Validate a UiPath Coded Action App `action-schema.json`.
 *
 * Single source of truth for action-schema rules in this skill. Mirrors the
 * authoritative validator shipped in the UiPath CLI:
 *   packages/codedapp-tool/src/types/action-app.ts  (JsonActionSchemaValidator)
 *
 * Do NOT restate the type / format / nesting rules in prose elsewhere in the
 * skill — point at this script and run it instead.
 *
 * Node-only (no dependencies). Node is already a skill prerequisite.
 *
 * Usage:
 *     node validate-action-schema.js <path/to/action-schema.json>
 *     node validate-action-schema.js -        # read JSON from stdin
 *     node validate-action-schema.js --show-types
 *
 * Exit codes:
 *     0  valid
 *     1  invalid  (one `path: message` per line on stderr)
 *     2  usage / IO / JSON-parse error
 *
 * Extending with a new field type (future-proofing):
 *     1. Add the JSON type name to SUPPORTED_TYPES.
 *     2. Add its System.* mapping to TYPE_SYSTEM_MAP (informational — mirrors the
 *        CLI's mapJsonTypeToSystemType; surfaced by --show-types).
 *     3. If it introduces a new `format`, add it to SUPPORTED_FORMATS (and, if the
 *        format may attach to a type other than `string`, extend
 *        FORMAT_ALLOWED_TYPES).
 *     The recursive property validator reads these tables — no other code changes.
 */

'use strict';

const fs = require('fs');

// --- Extensibility tables (keep in sync with the CLI enums) -----------------

// JsonDataType
const SUPPORTED_TYPES = ['string', 'integer', 'number', 'boolean', 'array', 'object', 'file'];

// JsonFormatType
const SUPPORTED_FORMATS = ['uuid', 'date'];

// Which field types each format may attach to. The CLI allows format only on
// `string` (uuid -> System.Guid, date -> System.DateOnly are string-encoded).
const FORMAT_ALLOWED_TYPES = {
  uuid: ['string'],
  date: ['string'],
};

// Informational: JsonDataType -> System.* type the CLI maps to. Not enforced;
// documents the runtime contract and powers --show-types.
const TYPE_SYSTEM_MAP = {
  string: 'System.String',
  integer: 'System.Int64',
  number: 'System.Decimal',
  boolean: 'System.Boolean',
  object: 'System.Object',
  file: 'UiPath.Platform.ResourceHandling.IResource',
  // `array` is a collection wrapper around its `items` type, not a System.* leaf.
};

const SECTIONS = ['inputs', 'outputs', 'inOuts', 'outcomes'];

// --- Validation -------------------------------------------------------------

function isPlainObject(value) {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function createErrors() {
  const errors = [];
  errors.add = (path, message) => errors.push(`  - ${path}: ${message}`);
  return errors;
}

function validateProperty(prop, path, errors) {
  if (!isPlainObject(prop)) {
    errors.add(path, 'property must be an object');
    return;
  }

  const ptype = prop.type;
  if (!SUPPORTED_TYPES.includes(ptype)) {
    errors.add(
      `${path}.type`,
      `type must be one of: ${SUPPORTED_TYPES.join(', ')} (got ${JSON.stringify(ptype)})`
    );
    // Can't reason further about a bad type.
    return;
  }

  if ('required' in prop && typeof prop.required !== 'boolean') {
    errors.add(`${path}.required`, 'required must be a boolean');
  }

  if ('description' in prop && typeof prop.description !== 'string') {
    errors.add(`${path}.description`, 'description must be a string');
  }

  const fmt = prop.format;
  if (fmt !== undefined && fmt !== null) {
    if (!SUPPORTED_FORMATS.includes(fmt)) {
      errors.add(
        `${path}.format`,
        `format must be one of: ${SUPPORTED_FORMATS.join(', ')} (got ${JSON.stringify(fmt)})`
      );
    } else if (!(FORMAT_ALLOWED_TYPES[fmt] || []).includes(ptype)) {
      errors.add(
        `${path}.format`,
        `'${fmt}' format is only allowed on type ` +
          `${(FORMAT_ALLOWED_TYPES[fmt] || []).join(' / ')} (type is '${ptype}')`
      );
    }
  }

  // Arrays: items required; nested arrays disallowed.
  if (ptype === 'array') {
    const items = prop.items;
    if (items === undefined || items === null) {
      errors.add(`${path}.items`, "array type requires an 'items' definition");
    } else {
      if (isPlainObject(items) && items.type === 'array') {
        errors.add(
          `${path}.items.type`,
          "nested arrays are not supported (an array's items.type cannot be 'array')"
        );
      }
      validateProperty(items, `${path}.items`, errors);
    }
  }

  // Validate nested object/array-of-object properties.
  const props = prop.properties;
  if (props !== undefined && props !== null) {
    if (!isPlainObject(props)) {
      errors.add(`${path}.properties`, 'properties must be an object');
    } else {
      for (const [childName, child] of Object.entries(props)) {
        validateProperty(child, `${path}.properties.${childName}`, errors);
      }
    }
  }
}

function validateSection(schema, name, errors) {
  if (!(name in schema)) {
    errors.add(name, 'missing required section');
    return;
  }
  const section = schema[name];
  if (!isPlainObject(section)) {
    errors.add(name, 'section must be an object');
    return;
  }
  if (section.type !== 'object') {
    errors.add(`${name}.type`, 'section "type" must be the literal "object"');
  }
  const props = section.properties;
  if (props === undefined || props === null) {
    errors.add(`${name}.properties`, "section must have a 'properties' object (use {} when empty)");
  } else if (!isPlainObject(props)) {
    errors.add(`${name}.properties`, "section 'properties' must be an object");
  } else {
    for (const [fieldName, field] of Object.entries(props)) {
      validateProperty(field, `${name}.properties.${fieldName}`, errors);
    }
  }
}

/** Return a list of error strings. Empty list == valid. */
function validateActionSchema(schema) {
  const errors = createErrors();
  if (!isPlainObject(schema)) {
    errors.add('root', 'action-schema must be a JSON object');
    return errors;
  }
  for (const name of SECTIONS) {
    validateSection(schema, name, errors);
  }
  return errors;
}

// --- CLI --------------------------------------------------------------------

function readStdin() {
  return fs.readFileSync(0, 'utf8');
}

function main(argv) {
  if (argv.includes('--show-types')) {
    process.stdout.write('Supported field types:\n');
    for (const t of SUPPORTED_TYPES) {
      const mapped = TYPE_SYSTEM_MAP[t] || '(collection of items type)';
      process.stdout.write(`  ${t.padEnd(8)} -> ${mapped}\n`);
    }
    process.stdout.write(`Supported formats (string only): ${SUPPORTED_FORMATS.join(', ')}\n`);
    return 0;
  }

  const args = argv.filter((a) => !a.startsWith('-'));
  if (args.length !== 1 && !(argv.length === 1 && argv[0] === '-')) {
    process.stderr.write('usage: validate-action-schema.js <action-schema.json | ->\n');
    return 2;
  }

  const source = argv.length ? argv[0] : '-';
  let raw;
  try {
    raw = source === '-' ? readStdin() : fs.readFileSync(source, 'utf8');
  } catch (exc) {
    process.stderr.write(`cannot read ${source}: ${exc.message}\n`);
    return 2;
  }

  let schema;
  try {
    schema = JSON.parse(raw);
  } catch (exc) {
    process.stderr.write(`invalid JSON: ${exc.message}\n`);
    return 2;
  }

  const errors = validateActionSchema(schema);
  if (errors.length) {
    process.stderr.write('Invalid action-schema.json:\n');
    process.stderr.write(errors.join('\n') + '\n');
    return 1;
  }

  process.stdout.write('action-schema.json is valid.\n');
  return 0;
}

if (require.main === module) {
  process.exit(main(process.argv.slice(2)));
}

module.exports = { validateActionSchema, SUPPORTED_TYPES, SUPPORTED_FORMATS };
