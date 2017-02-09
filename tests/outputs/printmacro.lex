keyword 'macro'
name 'printall'
symbol '('
name 'args'
symbol ')'
keyword 'as'
symbol '('
name 'args'
symbol ')'
indent
keyword 'let'
name 'node'
symbol '='
'table'
newline
name 'node'
symbol '.'
name 'tag'
symbol '='
string 'block'
newline
name 'node'
symbol '.'
name 'stmts'
symbol '='
'table'
newline
keyword 'save'
name 'node'
newline
keyword 'let'
name 'i'
symbol '='
int 0
newline
keyword 'let'
name 'call'
symbol '='
'null'
newline
keyword 'while'
name 'args'
symbol '['
name 'i'
symbol ']'
operator '!='
'null'
indent
name 'call'
symbol '='
'table'
newline
name 'call'
symbol '.'
name 'tag'
symbol '='
string 'call'
newline
name 'call'
symbol '.'
name 'func'
symbol '='
'table'
newline
name 'call'
symbol '.'
name 'func'
symbol '.'
name 'tag'
symbol '='
string 'name'
newline
name 'call'
symbol '.'
name 'func'
symbol '.'
name 'value'
symbol '='
string 'print'
newline
name 'call'
symbol '.'
name 'args'
symbol '='
'table'
newline
name 'call'
symbol '.'
name 'args'
symbol '['
int 0
symbol ']'
symbol '='
name 'args'
symbol '['
name 'i'
symbol ']'
newline
name 'node'
symbol '.'
name 'stmts'
symbol '['
name 'i'
symbol ']'
symbol '='
name 'call'
newline
name 'i'
symbol '='
name 'i'
operator '+'
int 1
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
symbol '@'
name 'printall'
symbol '('
string 'one'
symbol ','
string 'two'
symbol ','
string 'THREE'
symbol ','
string 'four'
symbol ')'
newline
dedent
newline
EOF
