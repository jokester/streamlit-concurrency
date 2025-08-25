## Streamlit Internals

### Terms

- BackMsg: browser > server
    - rerun_script / stop_script / etc . see `AppSession#handle_backmsg()`
- ForwardMsg: server > browser

### ClientState

- fragment_id
- ??

### Server

- a tornado HTTP + WS server
- a `class Runtime` singleton

### `class Runtime`: 1 per server

- sessions

### `AppSession`: 1 per connected browser tab

creation:  `class WebsocketSessionManager: def connectSession()`

fields:
- `_state` : RUNNING | NOT_RUNNING | SHUTDOWN_REQUESTED
- ScriptData
    - path to main script
- widget states
- DeltaGenerator
    - encode widget states and send to browser (encoded in PB, as WS msg)
- ScriptRunner (per script run)

methods:

- shutdown()
- `_enqueue_forward_msg()` : 

- server-bound 

### `struct RerunData`

- query_string
- page_script_hash
- context_info
- cached_messages

### ScriptRunner

creation: `AppSession#_create_scriptrunner()`, unless:
- fastRun disabled and a previous ScriptRunner existed
- OR, rerunning for a fragment

fields:

- initial_rerun_data
- `_requests()` a request queue
    - request types: `ScriptRequestType.{CONTINUE,STOP,RERUN}`
    - st.

#### with `fastReruns` enabled (the default)

- create new immediately
- old ScriptRunner if existed, are requested to stop , and dereferenced

#### request_stop()

- raise `RerunException` on next ForwardMsg queued (basically st.* API call)



### ScriptRunner without `fastReruns` enabled (the default)
 
- "wait 

### Fragment

- ???