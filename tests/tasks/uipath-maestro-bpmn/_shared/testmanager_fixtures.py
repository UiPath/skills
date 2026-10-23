"""HTTP node templates shared by the Test Manager checker tests."""

TM_KEY = "uipath-uipath-testmanager"

HTTP_NODE = """
    <bpmn:sendTask id="Task_{index}">
      <bpmn:extensionElements>
        <uipath:activity version="v1">
          <uipath:type value="Intsvc.UnifiedHttpRequest" version="v1" />
          <uipath:context>
            <uipath:input name="connectorKey" type="string" value="uipath-uipath-http" />
            <uipath:input name="method" type="string" value="POST" />
            <uipath:input name="path" type="string" value="/http-request" />
            <uipath:input name="objectName" type="string" value="http-request" />
          </uipath:context>
          <uipath:input name="body" type="json" target="body"><![CDATA[{body}]]></uipath:input>
        </uipath:activity>
      </bpmn:extensionElements>
    </bpmn:sendTask>"""

LEGACY_SDK_HTTP_NODE = """
    <bpmn:sendTask id="Task_{index}">
      <bpmn:extensionElements>
        <uipath:activity version="v1">
          <uipath:type value="Intsvc.ActivityExecution" version="v1" />
          <uipath:context>
            <uipath:input name="connectorKey" type="string" value="uipath-uipath-testmanager" />
            <uipath:input name="objectName" type="string" value="http-request" />
            <uipath:input name="method" type="string" value="POST" />
            <uipath:input name="path" type="string" value="/http-request" />
          </uipath:context>
          <uipath:input name="body" type="json" target="body"><![CDATA[{body}]]></uipath:input>
        </uipath:activity>
      </bpmn:extensionElements>
    </bpmn:sendTask>"""
