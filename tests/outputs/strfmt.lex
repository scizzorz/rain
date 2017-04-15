keyword 'var'
name 'main'
symbol '='
keyword 'func'
symbol '('
symbol ')'
indent
keyword 'var'
name 'a'
symbol '='
int -3
newline
keyword 'var'
name 'b'
symbol '='
int 3
newline
keyword 'var'
name 'args'
symbol '='
'table'
newline
name 'args'
symbol '['
int 0
symbol ']'
symbol '='
string 'zero'
newline
name 'args'
symbol '['
int 1
symbol ']'
symbol '='
string 'one'
newline
name 'args'
symbol '.'
name 'name'
symbol '='
string 'John'
newline
name 'args'
symbol '.'
name 'exc'
symbol '='
name 'except'
symbol '.'
name 'argmismatch'
newline
name 'print'
symbol '('
string 'String substitution: {name}'
symbol ':'
name 'fmt'
symbol '('
name 'args'
symbol ')'
symbol ')'
newline
name 'print'
symbol '('
string 'String coercion: {exc}'
symbol ':'
name 'fmt'
symbol '('
name 'args'
symbol ')'
symbol ')'
newline
name 'print'
symbol '('
string 'Implicit counting: {} {}'
symbol ':'
name 'fmt'
symbol '('
name 'args'
symbol ')'
symbol ')'
newline
name 'print'
symbol '('
string 'Explicit counting: {1} {0}'
symbol ':'
name 'fmt'
symbol '('
name 'args'
symbol ')'
symbol ')'
newline
name 'print'
symbol '('
string 'Mixed counting: {} {name} {} {1} {0}'
symbol ':'
name 'fmt'
symbol '('
name 'args'
symbol ')'
symbol ')'
newline
dedent
newline
EOF
