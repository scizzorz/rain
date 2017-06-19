keyword 'import'
name 'moda'
newline
keyword 'var'
name 'init'
symbol '='
keyword 'func'
symbol '('
symbol ')'
indent
name 'print'
symbol '('
string 'modb init()'
symbol ')'
newline
dedent
newline
keyword 'var'
name 'test'
symbol '='
keyword 'func'
symbol '('
symbol ')'
indent
name 'print'
symbol '('
string 'modb.name = '
operator '$'
name 'exports'
symbol '.'
name 'name'
symbol ')'
newline
dedent
newline
keyword 'var'
name 'main'
symbol '='
keyword 'func'
symbol '('
symbol ')'
indent
name 'print'
symbol '('
string 'modb.main()'
symbol ')'
newline
name 'moda'
symbol '.'
name 'test'
symbol '('
symbol ')'
newline
name 'test'
symbol '('
symbol ')'
newline
name 'moda'
symbol '.'
name 'name'
symbol '='
string 'new a module'
newline
name 'exports'
symbol '.'
name 'name'
symbol '='
string 'new b module'
newline
name 'moda'
symbol '.'
name 'test'
symbol '('
symbol ')'
newline
name 'test'
symbol '('
symbol ')'
newline
dedent
newline
name 'exports'
symbol '='
'table'
symbol '{'
name 'name'
symbol '='
string 'module b'
symbol ','
name 'test'
symbol '='
name 'test'
symbol ','
name 'main'
symbol '='
name 'main'
symbol ','
symbol '}'
newline
EOF
