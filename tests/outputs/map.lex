keyword 'import'
string 'types/array'
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
symbol '['
int 10
symbol ','
int 11
symbol ','
int 12
symbol ','
int 13
symbol ']'
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
string 'key/values from b:'
symbol ')'
newline
keyword 'for'
symbol '['
name 'k'
symbol ','
name 'v'
symbol ']'
keyword 'in'
name 'b'
symbol ':'
name 'items'
symbol '('
symbol ')'
indent
name 'print'
symbol '('
name 'tostr'
symbol '('
name 'k'
symbol ')'
operator '$'
string ' = '
operator '$'
name 'tostr'
symbol '('
name 'v'
symbol ')'
symbol ')'
newline
dedent
newline
dedent
newline
EOF
