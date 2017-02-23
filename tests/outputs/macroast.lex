keyword 'import'
name 'ast'
newline
keyword 'macro'
name 'expr'
symbol '('
name 'expr'
symbol ')'
keyword 'as'
symbol '('
name 'expr'
symbol ')'
indent
keyword 'return'
name 'expr'
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
keyword 'let'
name 'x'
symbol '='
symbol '@'
name 'expr'
string 'This better work.'
newline
name 'print'
symbol '('
name 'x'
symbol ')'
newline
dedent
newline
EOF
