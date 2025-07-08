// filepath: /Users/mac/WORKSPACE/cognihub_pygotemplate/cognihub_pygotemplate/renderer.go
package main

import "C"
import (
	"bytes"
	"encoding/json"
	"sync"
	"text/template"
	"unsafe"
)

var (
	stringPool = make(map[uintptr]*C.char)
	poolMutex  sync.Mutex
)

//export RenderTemplate
func RenderTemplate(templateStr *C.char, jsonData *C.char) *C.char {
	goTemplateStr := C.GoString(templateStr)
	goJsonData := C.GoString(jsonData)

	var data interface{}
	if err := json.Unmarshal([]byte(goJsonData), &data); err != nil {
		return storeString("JSON_ERROR: " + err.Error())
	}

	tmpl, err := template.New("ollama").Parse(goTemplateStr)
	if err != nil {
		return storeString("TEMPLATE_PARSE_ERROR: " + err.Error())
	}

	var renderedBytes bytes.Buffer
	if err := tmpl.Execute(&renderedBytes, data); err != nil {
		return storeString("TEMPLATE_EXECUTE_ERROR: " + err.Error())
	}

	return storeString(renderedBytes.String())
}

func storeString(s string) *C.char {
	cstr := C.CString(s)
	poolMutex.Lock()
	stringPool[uintptr(unsafe.Pointer(cstr))] = cstr
	poolMutex.Unlock()
	return cstr
}

//export FreeString
func FreeString(str *C.char) {
	if str == nil {
		return
	}

	ptr := uintptr(unsafe.Pointer(str))
	poolMutex.Lock()
	if _, exists := stringPool[ptr]; exists {
		delete(stringPool, ptr)
	}
	poolMutex.Unlock()
}

func main() {}
