keyword 'import'
name 'env'
newline
keyword 'import'
name 'array'
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
name 'array'
symbol '.'
name 'length'
symbol '('
name 'env'
symbol '.'
name 'args'
symbol ')'
symbol ')'
newline
keyword 'for'
name 'arg'
keyword 'in'
name 'array'
symbol '.'
name 'values'
symbol '('
name 'env'
symbol '.'
name 'args'
symbol ')'
indent
name 'print'
symbol '('
name 'arg'
symbol ')'
newline
dedent
newline
name 'print'
symbol '('
string '$RAIN_TEST = '
operator '$'
name 'env'
symbol '.'
name 'get'
symbol '('
string 'RAIN_TEST'
symbol ')'
symbol ')'
newline
dedent
newline
EOF
