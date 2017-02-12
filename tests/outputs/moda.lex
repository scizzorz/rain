keyword 'import'
name 'modb'
newline
keyword 'export'
name 'name'
symbol '='
string 'module a'
newline
keyword 'export'
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
keyword 'export'
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
name 'name'
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
EOF
