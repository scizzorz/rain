keyword 'macro'
name 'test'
symbol '('
name 'expr'
symbol ','
name 'block'
symbol ')'
keyword 'as'
symbol '('
name 'pred'
symbol ','
name 'body'
symbol ')'
indent
keyword 'return'
name 'ast'
symbol '.'
name 'if'
symbol ':'
name 'init'
symbol '('
name 'pred'
symbol ','
name 'body'
symbol ','
'null'
symbol ')'
newline
dedent
newline
keyword 'let'
name 'test'
symbol '='
keyword 'func'
symbol '('
name 'n'
symbol ')'
indent
symbol '@'
name 'test'
name 'n'
operator '>'
int 0
indent
name 'print'
symbol '('
string 'n > 0'
symbol ')'
newline
dedent
newline
symbol '@'
name 'test'
name 'n'
operator '<'
int 0
indent
name 'print'
symbol '('
string 'n < 0'
symbol ')'
newline
dedent
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
name 'test'
symbol '('
int 10
symbol ')'
newline
name 'test'
symbol '('
operator '-'
int 10
symbol ')'
newline
name 'print'
symbol '('
string 'Done'
symbol ')'
newline
dedent
newline
EOF
