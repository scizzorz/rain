keyword 'var'
name 'main'
symbol '='
keyword 'func'
symbol '('
symbol ')'
indent
keyword 'var'
name 'obj'
symbol '='
symbol '{'
name 'one'
symbol '='
string 'one'
symbol ','
name 'two'
symbol '='
string 'two'
symbol ','
symbol '['
int 3
symbol ']'
symbol '='
string 'three'
symbol ','
symbol '['
string 'fo_ur'
symbol ']'
symbol '='
string 'four'
symbol '}'
newline
keyword 'for'
name 'a'
keyword 'in'
name 'obj'
symbol ':'
name 'keys'
symbol '('
symbol ')'
indent
name 'print'
symbol '('
string 'a: '
operator '$'
name 'tostr'
symbol '('
name 'a'
symbol ')'
symbol ')'
newline
keyword 'for'
name 'b'
keyword 'in'
name 'obj'
symbol ':'
name 'keys'
symbol '('
symbol ')'
indent
name 'print'
symbol '('
string '  b: '
operator '$'
name 'tostr'
symbol '('
name 'b'
symbol ')'
symbol ')'
newline
dedent
newline
dedent
newline
name 'print'
symbol '('
string '----------------------------------------'
symbol ')'
newline
keyword 'for'
name 'a'
keyword 'in'
name 'obj'
symbol ':'
name 'values'
symbol '('
symbol ')'
indent
name 'print'
symbol '('
string 'a: '
operator '$'
name 'a'
symbol ')'
newline
keyword 'for'
name 'b'
keyword 'in'
name 'obj'
symbol ':'
name 'values'
symbol '('
symbol ')'
indent
name 'print'
symbol '('
string '  b: '
operator '$'
name 'b'
symbol ')'
newline
dedent
newline
dedent
newline
dedent
newline
EOF
