import test_parser
import utils

for file in utils.lsrn(test_parser.TEST_DIR):
  output = utils.parse(file)
  with open(file + '.yml', 'w') as fp:
    fp.write(output)
