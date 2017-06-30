keyword 'import'
name 'modb'
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
string 'moda init()'
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
string 'moda.name = '
operator '$'
name 'module'
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
string 'moda.main()'
symbol ')'
newline
name 'test'
symbol '('
symbol ')'
newline
name 'modb'
symbol '.'
name 'test'
symbol '('
symbol ')'
newline
name 'module'
symbol '.'
name 'name'
symbol '='
string 'new a module'
newline
name 'modb'
symbol '.'
name 'name'
symbol '='
string 'new b module'
newline
name 'test'
symbol '('
symbol ')'
newline
name 'modb'
symbol '.'
name 'test'
symbol '('
symbol ')'
newline
dedent
newline
name 'module'
symbol '='
'table'
symbol '{'
name 'name'
symbol '='
string 'module a'
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
