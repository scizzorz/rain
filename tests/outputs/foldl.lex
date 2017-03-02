keyword 'import'
string 'types/array'
newline
keyword 'let'
name 'gadd'
symbol '='
keyword 'func'
symbol '('
name 'a'
symbol ','
name 'b'
symbol ')'
operator '->'
name 'a'
operator '+'
name 'b'
newline
keyword 'let'
name 'main'
symbol '='
keyword 'func'
symbol '('
symbol ')'
indent
keyword 'let'
name 'ladd'
symbol '='
keyword 'func'
symbol '('
name 'a'
symbol ','
name 'b'
symbol ')'
operator '->'
name 'a'
operator '+'
name 'b'
newline
keyword 'let'
name 'a'
symbol '='
symbol '['
int 1
symbol ','
int 2
symbol ','
int 3
symbol ']'
newline
name 'print'
symbol '('
name 'a'
symbol ':'
name 'foldl'
symbol '('
name 'gadd'
symbol ','
int 0
symbol ')'
symbol ')'
newline
name 'print'
symbol '('
name 'a'
symbol ':'
name 'foldl'
symbol '('
name 'ladd'
symbol ','
int 0
symbol ')'
symbol ')'
newline
dedent
newline
EOF
