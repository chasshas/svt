# SVT v1.1.1 — Scriptable Virtual Terminal

순수 Python 플러그인 기반 터미널. 모든 기능이 `앱:커맨드` 형태의 독립 앱으로 존재합니다.

## 실행

```bash
python -m main.py svt                    # 인터랙티브 REPL
python -m main.py script.svt         # 스크립트 실행
python -m main.py -e "io:print Hi"   # 인라인 실행
```

## 프로젝트 구조

```
svt/
├── main.py              # 진입점
├── core/                # 엔진 (파서, 디스패처, 블록 수집)
├── sdk/                 # 앱 개발용 SDK (ExecutionContext, VariableStore, EventBus)
├── apps/                # 내장 앱 15개 (272개 커맨드)
│   ├── sys/   var/   io/   flow/   exec/   event/   math/   shell/
│   ├── str/   time/  log/  list/   map/    net/     file/
├── docs/                # 상세 문서
│   ├── architecture.md      # 아키텍처 심층 분석
│   ├── app-development.md   # 앱 개발 가이드
│   ├── command-reference.md # 전체 커맨드 레퍼런스 (272개)
│   └── data-structures.md   # 자료구조 / 파일 형식
├── CLAUDE.md            # Claude Code 프로젝트 컨텍스트
├── AGENTS.md            # 범용 AI 에이전트 컨텍스트
├── .cursorrules         # Cursor IDE 규칙
├── .windsurfrules       # Windsurf 규칙
└── .github/copilot-instructions.md
```

## 문법

```bash
앱:커맨드 인자1 "인자2" --옵션 값     # 기본 호출
var:set x 10                          # 변수 설정
io:print "Hello $x"                   # 더블쿼트: 변수치환 O
var:set r $(math:add $x 20)           # $(...) 커맨드 치환
exec:lines 'cmd1; cmd2'              # 싱글쿼트: 리터럴 (치환 X)
```

## 오브젝트 (Dictionary)

```bash
var:obj_new user
var:obj_set user name "Alice"
io:print "$user.name"                  # 도트 표기법
io:print "${user.name}"                # 중괄호 형태
flow:for key in user                   # dict 키 순회
  io:print "$key = $(var:obj_get user $key)"
flow:end
```

## 변수 스코프

```bash
var:set x 100                          # 글로벌
var:scope_push                         # 로컬 스코프 생성
var:local y 200                        # 현재 스코프에만
var:global g 777                       # 항상 글로벌에
var:scope_pop                          # y 소멸
```

## 흐름 제어

```bash
flow:if $x == 42          flow:while $i < 5       flow:for n in 1..10
  io:print "yes"            var:incr i               io:print "$n"
flow:elif $x > 42         flow:end                 flow:end
  io:print "high"
flow:else
  io:print "low"
flow:end

flow:try                               flow:throw "에러 메시지"
  flow:throw "problem"
flow:catch err
  io:print "잡음: $err"
flow:finally
  io:print "항상 실행"
flow:end
```

## Shell (OS 연동)

```bash
var:set files $(shell:exec ls -la)     # stdout 캡처
shell:run make build                    # 실시간 출력
shell:pipe ver uname -r                 # 변수에 저장
shell:cd /tmp                           # 디렉토리 이동
var:set home $(shell:env HOME)          # 환경변수
```

## Math (41개 커맨드)

산술(`add sub mul div mod pow abs max min range`),
삼각함수(`sin cos tan asin acos atan atan2 deg rad`),
로그(`log log2 log10 exp`), 제곱근(`sqrt cbrt`),
반올림(`ceil floor round trunc`), 상수(`pi e tau inf`),
난수(`rand randint`), 집계(`sum avg`), 변환(`hex bin int float`)

## 이벤트 시스템

```bash
event:on var.changed.score 'io:print "변경!"'
var:set score 100                      # → "변경!"
event:emit custom_event
```

## 내장 앱 요약 (15개, 272개 커맨드)

| 앱 | 수 | 설명 |
|----|-----|------|
| sys | 7 | exit, help, apps, version, info, reload, clear |
| var | 22 | set/get/del + scope + obj (dict) |
| io | 4 | print, println, input, error |
| flow | 12 | if/elif/else, while, for, try/catch/finally, throw |
| exec | 4 | run, eval, lines, file |
| event | 6 | on, once, off, emit, list, clear |
| math | 41 | 산술, 삼각함수, 로그, 반올림, 상수, 난수, 변환 |
| shell | 9 | exec, run, pipe, env, setenv, cd, pwd, which, exit_code |
| str | 31 | upper/lower/title, strip, split, join, replace, find, contains, startswith/endswith, len, slice, count, repeat, reverse, pad, chars, lines, format, is*, sub/match/extract (regex) |
| time | 28 | now, today, timestamp, parse, format, add/sub/diff, year/month/day/hour/minute/second, weekday, is_leap, sleep, perf, make, compare, between, timezone |
| log | 22 | debug/info/warning/error/critical, log, level, format, name, add_file/remove_file, add/remove_console, handlers, history, tail, enable/disable, reset, stats |
| list | 30 | new, push, pop, get, set, del, len, sort, reverse, slice, contains, index, count, insert, extend, flatten, unique, join, head, tail, zip, sum/min/max/avg, filter, map_str, range, sample, shuffle |
| map | 20 | new, set, get, del, has, keys, values, items, len, merge, pop, select, omit, invert, from_pairs, from_lists, update, contains_value, json, from_json |
| net | 12 | get, post, headers, resolve, ping, scan, ip, download, urlencode, urldecode, base64enc, base64dec |
| file | 24 | read, write, append, copy, move, rm, mkdir, ls, exists, isfile, isdir, stat, size, ext, basename, dirname, abspath, join, find, grep, lines, touch, tempdir, tempfile |

## 앱 개발

`docs/app-development.md` 참고. 요약:

```python
# apps/myapp/app.py
from svt.sdk import SVTApp, CommandResult, ExecutionContext

class MyApp(SVTApp):
    def cmd_hello(self, ctx: ExecutionContext) -> CommandResult:
        name = str(ctx.args[0]) if ctx.args else "World"
        print(f"Hello, {name}!")
        return CommandResult.success(value=name)