# Log files for the command-line drills and the log analyser

All data here is invented.

- `server.log`: a short web server log for command-line drill 1 (head, tail -f, grep -i).
- `messy.log`: the log for the day 3 log analyser. Each good line is `TIMESTAMP LEVEL MODULE MESSAGE`, for example `2026-03-02T08:00:12 INFO auth login ok user=u101`. The level is DEBUG, INFO, WARNING or ERROR. Some lines are broken on purpose: count them and report them, and never let them crash the tool.
