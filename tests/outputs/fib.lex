keyword 'let'
name 'fib'
symbol '='
keyword 'func'
symbol '('
name 'n'
symbol ')'
indent
keyword 'if'
name 'n'
operator '<='
int 1
indent
keyword 'return'
int 1
newline
dedent
newline
keyword 'return'
name 'fib'
symbol '('
name 'n'
operator '-'
int 1
symbol ')'
operator '+'
name 'fib'
symbol '('
name 'n'
operator '-'
int 2
symbol ')'
newline
dedent
newline
keyword 'let'
name 'main'
symbol '='
keyword 'func'
symbol '('
symbol ')'
indent
name 'print'
symbol '('
name 'fib'
symbol '('
int 10
symbol ')'
symbol ')'
newline
dedent
newline
EOF
