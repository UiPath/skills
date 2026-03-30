---
confidence: medium
---

# File Handling Issues

## Context

What this looks like:
- "Attachment not found"
- File inputs not working or not passed correctly between tasks
- Files not appearing in the debug input panel

What can cause it:
- File inputs defined as variables instead of arguments — files must be passed as arguments to appear in the debug input panel
- Job retention policy deleting the job that owns an attachment (see attachment-not-found playbook for retention-specific cases)
- Box connector "Update Variables" option not saving the source value in XML for File types (frontend bug in IntsvcActivityConfig v2)
- File type incompatibility between ILocalResource (Studio Desktop) and File (Studio Web) with newer agent expectations
- Robot version incompatibility — older Robot versions do not produce File objects with metadata that agents expect

What to look for:
- Check if files are defined as arguments or variables
- Check Robot version compatibility
- Check if the issue is in debug, deployed, or both

## Investigation

1. Check if file inputs are defined as arguments (not variables) in the BPMN process
2. Check Robot version against Studio Web requirements
3. For Box connector: check if the "Update Variables" XML contains the correct source value for File types
4. Check if the file is being passed between tasks or downloaded from an external source (Data Fabric, storage bucket)

## Resolution

- **If variable vs argument:** change file inputs to arguments instead of variables
- **If version mismatch:** upgrade Robot to the latest version
- **If Box connector bug:** manually fix the XML source value as a workaround
- **If file passing between tasks:** redesign to download files from source (e.g., Data Fabric) in each task instead of passing file references
