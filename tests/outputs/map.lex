keyword 'import'
name 'array'
newline
keyword 'import'
name 'iter'
newline
keyword 'let'
name 'double'
symbol '='
keyword 'func'
symbol '('
name 'n'
symbol ')'
operator '->'
name 'n'
operator '*'
int 2
newline
keyword 'let'
name 'main'
symbol '='
keyword 'func'
symbol '('
symbol ')'
indent
keyword 'let'
name 'a'
symbol '='
'table'
operator '::'
name 'array'
newline
name 'a'
symbol '['
int 0
symbol ']'
symbol '='
int 10
newline
name 'a'
symbol '['
int 1
symbol ']'
symbol '='
int 11
newline
name 'a'
symbol '['
int 2
symbol ']'
symbol '='
int 12
newline
name 'a'
symbol '['
int 3
symbol ']'
symbol '='
int 13
newline
name 'print'
symbol '('
string 'keys from a:'
symbol ')'
newline
keyword 'for'
name 'x'
keyword 'in'
name 'a'
symbol ':'
name 'keys'
symbol '('
symbol ')'
indent
name 'print'
symbol '('
name 'x'
symbol ')'
newline
dedent
newline
name 'print'
symbol '('
string 'values from a:'
symbol ')'
newline
keyword 'for'
name 'x'
keyword 'in'
name 'a'
symbol ':'
name 'values'
symbol '('
symbol ')'
indent
name 'print'
symbol '('
name 'x'
symbol ')'
newline
dedent
newline
name 'print'
symbol '('
string 'doubled values from a:'
symbol ')'
newline
keyword 'for'
name 'x'
keyword 'in'
name 'iter'
symbol '.'
name 'map'
symbol '('
name 'a'
symbol ':'
name 'values'
symbol '('
symbol ')'
symbol ','
name 'double'
symbol ')'
indent
name 'print'
symbol '('
name 'x'
symbol ')'
newline
dedent
newline
keyword 'let'
name 'b'
symbol '='
name 'a'
symbol ':'
name 'map'
symbol '('
name 'double'
symbol ')'
newline
name 'print'
symbol '('
string 'keys from b:'
symbol ')'
newline
keyword 'for'
name 'x'
keyword 'in'
name 'b'
symbol ':'
name 'keys'
symbol '('
symbol ')'
indent
name 'print'
symbol '('
name 'x'
symbol ')'
newline
dedent
newline
name 'print'
symbol '('
string 'values from b:'
symbol ')'
newline
keyword 'for'
name 'x'
keyword 'in'
name 'b'
symbol ':'
name 'values'
symbol '('
symbol ')'
indent
name 'print'
symbol '('
name 'x'
symbol ')'
newline
dedent
newline
dedent
newline
EOF
