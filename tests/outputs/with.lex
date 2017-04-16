keyword 'var'
name 'ctx0'
symbol '='
keyword 'func'
symbol '('
name 'block'
symbol ')'
indent
name 'print'
symbol '('
string 'Initialization'
symbol ')'
newline
name 'block'
symbol '('
symbol ')'
newline
name 'print'
symbol '('
string 'Clean up'
symbol ')'
newline
dedent
newline
keyword 'var'
name 'ctx1'
symbol '='
keyword 'func'
symbol '('
name 'block'
symbol ')'
indent
name 'print'
symbol '('
string 'Initialization'
symbol ')'
newline
name 'block'
symbol '('
string 'One'
symbol ')'
newline
name 'block'
symbol '('
string 'Two'
symbol ')'
newline
name 'print'
symbol '('
string 'Clean up'
symbol ')'
newline
dedent
newline
keyword 'var'
name 'ctx2'
symbol '='
keyword 'func'
symbol '('
name 'block'
symbol ')'
indent
name 'print'
symbol '('
string 'Initialization'
symbol ')'
newline
name 'block'
symbol '('
string 'One'
symbol ','
string '1'
symbol ')'
newline
name 'block'
symbol '('
string 'Two'
symbol ','
string '2'
symbol ')'
newline
name 'print'
symbol '('
string 'Clean up'
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
keyword 'with'
name 'ctx0'
indent
name 'print'
symbol '('
string 'Anonymous block'
symbol ')'
newline
dedent
newline
keyword 'with'
name 'ctx1'
keyword 'as'
name 'a'
indent
name 'print'
symbol '('
string 'Anonymous block: '
operator '$'
name 'a'
symbol ')'
newline
dedent
newline
keyword 'with'
name 'ctx2'
keyword 'as'
name 'a'
symbol ','
name 'b'
indent
name 'print'
symbol '('
string 'Anonymous block: '
operator '$'
name 'a'
operator '$'
string ' + '
operator '$'
name 'b'
symbol ')'
newline
dedent
newline
dedent
newline
EOF
