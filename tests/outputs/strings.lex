keyword 'var'
name 'main'
symbol '='
keyword 'func'
symbol '('
symbol ')'
indent
keyword 'var'
name 's'
symbol '='
string 'Hello'
newline
keyword 'var'
name 'p'
symbol '='
string 'world'
newline
keyword 'var'
name 'sp'
symbol '='
name 's'
operator '$'
string ', '
operator '$'
name 'p'
newline
name 'print'
symbol '('
name 'sp'
symbol ')'
newline
keyword 'var'
name 'i'
symbol '='
operator '-'
name 'sp'
symbol ':'
name 'length'
symbol '('
symbol ')'
operator '-'
int 1
newline
keyword 'while'
name 'i'
operator '<'
name 'sp'
symbol ':'
name 'length'
symbol '('
symbol ')'
operator '+'
int 1
indent
name 'print'
symbol '('
string '['
operator '$'
name 'tostr'
symbol '('
name 'i'
symbol ')'
operator '$'
string '] = '
operator '$'
name 'tostr'
symbol '('
name 'sp'
symbol '['
name 'i'
symbol ']'
symbol ')'
symbol ')'
newline
name 'i'
symbol '='
name 'i'
operator '+'
int 1
newline
dedent
newline
name 'print'
symbol '('
name 'sp'
symbol '['
symbol '['
int 0
symbol ','
int 4
symbol ']'
symbol ']'
symbol ')'
newline
name 'print'
symbol '('
name 'sp'
symbol '['
symbol '['
int 2
symbol ','
int 6
symbol ']'
symbol ']'
symbol ')'
newline
name 'print'
symbol '('
name 'sp'
symbol '['
symbol '['
int 2
symbol ','
int -1
symbol ']'
symbol ']'
symbol ')'
newline
name 'print'
symbol '('
name 'sp'
symbol '['
symbol '['
int -4
symbol ','
int -1
symbol ']'
symbol ']'
symbol ')'
newline
name 'print'
symbol '('
name 'sp'
symbol '['
symbol '['
int -8
symbol ','
int 8
symbol ']'
symbol ']'
symbol ')'
newline
name 'print'
symbol '('
name 'sp'
symbol '['
symbol '['
int 2
symbol ','
name 'sp'
symbol ':'
name 'length'
symbol '('
symbol ')'
symbol ']'
symbol ']'
symbol ')'
newline
name 'print'
symbol '('
name 'sp'
symbol '['
symbol '['
int 2
symbol ','
name 'sp'
symbol ':'
name 'length'
symbol '('
symbol ')'
operator '+'
int 2
symbol ']'
symbol ']'
symbol ')'
newline
name 'print'
symbol '('
name 'sp'
symbol '['
symbol '['
int 15
symbol ','
int 12
symbol ']'
symbol ']'
symbol ')'
newline
name 'print'
symbol '('
name 'sp'
symbol '['
symbol '['
int 4
symbol ','
int 3
symbol ']'
symbol ']'
symbol ')'
newline
dedent
newline
EOF
