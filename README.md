# SVT — Scriptable Virtual Terminal

순수 Python으로 구현된 플러그인 기반 터미널 애플리케이션.
모든 기능이 **앱(App)** 단위로 분리되어 있으며, `앱:커맨드` 형식으로 호출합니다.

## 실행 방법

```bash
# svt/ 폴더의 상위 디렉토리에서:
python -m svt                    # 인터랙티브 REPL
python -m svt script.svt         # 스크립트 파일 실행
python -m svt -e "io:print Hi"   # 인라인 커맨드 실행
```

## 프로젝트 구조

```
svt/
├── main.py                 # 진입점
├── core/
│   ├── interpreter.py      # 토크나이저 + 파서
│   ├── engine.py           # 실행 엔진 (REPL, 블록, 디스패치)
│   └── loader.py           # 앱 디스커버리 및 로딩
├── sdk/
│   ├── types.py            # AppManifest, CommandResult, BlockData
│   ├── context.py          # ExecutionContext, VariableStore, EventBus
│   └── base.py             # SVTApp 베이스 클래스
└── apps/                   # 내장 앱
    ├── sys/   var/   io/   flow/   exec/   event/   math/
```

## 문법 요약

```bash
앱:커맨드 인자1 "인자2" --옵션 값       # 기본 호출
var:set x 10                            # 변수 설정
io:print "Hello $x"                     # 더블쿼트: 변수 치환 O
var:set r $(math:add $x 20)             # $(...) 커맨드 치환
exec:lines 'cmd1; cmd2; cmd3'           # 싱글쿼트: 리터럴 (치환 X)
```

## 흐름 제어

```bash
# 조건문                     # While 루프                # For 루프
flow:if $x == 42             flow:while $i < 5           flow:for n in 1..10
  io:print "yes"               var:incr i                  io:print "$n"
flow:elif $x > 42            flow:end                    flow:end
  io:print "high"
flow:else                    # 연산자: == != < > <= >=
  io:print "low"             #         && || !
flow:end
```

## 이벤트 시스템

```bash
event:on var.changed.score 'io:print "changed!"'
var:set score 100   # → "changed!" 출력
event:emit custom_event
```

## 앱 개발

### Python 앱

`apps/myapp/app.json`:
```json
{"name":"myapp","type":"python","commands":{"hello":{"description":"Say hi"}}}
```

`apps/myapp/app.py`:
```python
from svt.sdk import SVTApp, CommandResult, ExecutionContext

class MyApp(SVTApp):
    def cmd_hello(self, ctx: ExecutionContext) -> CommandResult:
        name = ctx.args[0] if ctx.args else "World"
        print(f"Hello, {name}!")
        return CommandResult.success(value=name)
```

### Script 앱

`apps/myapp/greet.svt` (첫 줄에 인자/옵션 선언):
```bash
#!svt name:string --greeting/-g:string=Hello
io:print "${greeting}, ${name}!"
```

### SDK 핵심 API

- `ctx.args` / `ctx.options` — 파싱된 인자/옵션
- `ctx.variables` — VariableStore (set/get/delete/exists/list_all)
- `ctx.events` — EventBus (on/off/emit)
- `ctx.execute("cmd")` / `ctx.execute_lines([...])` — 커맨드 실행
- `CommandResult.success(value=...)` / `.error(msg)` / `.exit_signal(code)`
