<!--skill-flavor:bpmn-project-structure:start-->
<!-- Editable source layout in Studio Web: the project lives in the open solution under `/solution`, and its
     `.bpmn.ts` source sits in the project's `.flow-sdk/` folder under the main .bpmn's basename (Studio Web
     names a new project's main file `Process.bpmn`). Compile it into that .bpmn; never hand-edit the compiled .bpmn. bindings_v2.json, entry-points.json, operate.json,
     package-descriptor.json are generated/CLI-managed package metadata — never scaffolded by hand. -->

```text
/solution/
└── <BPMN_PROJECT_NAME>/
    ├── .flow-sdk/
    │   └── <BPMN_MAIN_FILE>.bpmn.ts   # source: edit this, then compile
    ├── <BPMN_MAIN_FILE>.bpmn          # compiled output: the project's main file
    └── project.uiproj
```
<!--skill-flavor:bpmn-project-structure:end-->
