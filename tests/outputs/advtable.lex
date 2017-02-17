keyword 'import'
name 'array'
newline
keyword 'import'
name 'dict'
newline
keyword 'let'
name 'ga'
symbol '='
symbol '['
int 1
symbol ','
int 2
symbol ','
int 3
symbol ']'
newline
keyword 'let'
name 'gd'
symbol '='
symbol '{'
name 'greeting'
symbol '='
string 'Good day.'
symbol ','
symbol '['
string 'name'
symbol ']'
symbol '='
string 'John'
symbol ','
name 'age'
symbol '='
int 24
symbol ','
symbol '['
int 1
symbol ']'
symbol '='
string 'One'
symbol '}'
newline
keyword 'let'
name 'main'
symbol '='
keyword 'func'
symbol '('
symbol ')'
indent
keyword 'let'
name 'la'
symbol '='
symbol '['
int 4
symbol ','
int 5
symbol ','
int 6
symbol ','
symbol ']'
newline
keyword 'let'
name 'ld'
symbol '='
symbol '{'
name 'greeting'
symbol '='
string 'Hello!'
symbol ','
symbol '['
string 'name'
symbol ']'
symbol '='
string 'Phil'
symbol ','
name 'age'
symbol '='
int 27
symbol ','
symbol '['
name 'la'
symbol '['
int 0
symbol ']'
symbol ']'
symbol '='
string 'Four'
symbol ','
symbol '}'
newline
keyword 'for'
name 'val'
keyword 'in'
name 'ga'
symbol ':'
name 'values'
symbol '('
symbol ')'
indent
name 'print'
symbol '('
name 'val'
symbol ')'
newline
dedent
newline
keyword 'for'
name 'val'
keyword 'in'
name 'la'
symbol ':'
name 'values'
symbol '('
symbol ')'
indent
name 'print'
symbol '('
name 'val'
symbol ')'
newline
dedent
newline
name 'print'
symbol '('
name 'gd'
symbol '.'
name 'name'
operator '$'
string ' says '
operator '$'
name 'gd'
symbol '.'
name 'greeting'
symbol ')'
newline
name 'print'
symbol '('
name 'gd'
symbol '['
int 1
symbol ']'
symbol ')'
newline
name 'print'
symbol '('
name 'ld'
symbol '.'
name 'name'
operator '$'
string ' says '
operator '$'
name 'ld'
symbol '.'
name 'greeting'
symbol ')'
newline
name 'print'
symbol '('
name 'ld'
symbol '['
int 4
symbol ']'
symbol ')'
newline
dedent
newline
EOF
