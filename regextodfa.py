from copy import deepcopy

#Regex validation
def is_valid_regex(regex):
    return valid_brackets(regex) and valid_operations(regex)


def valid_brackets(regex):
    opened_brackets = 0
    for c in regex:
        if c == '(':
            opened_brackets += 1
        if c == ')':
            opened_brackets -= 1
        if opened_brackets < 0:
            print('ERROR missing bracket')
            return False
    if opened_brackets == 0:
        return True
    print('ERROR unclosed brackets')
    return False


def valid_operations(regex):
    for i, c in enumerate(regex):
        if c == '*':
            if i == 0:
                print('ERROR * with no argument at', i)
                return False
            if regex[i - 1] in '(|':
                print('ERROR * with no argument at', i)
                return False
        if c == '|':
            if i == 0 or i == len(regex) - 1:
                print('ERROR | with missing argument at', i)
                return False
            if regex[i - 1] in '(|':
                print('ERROR | with missing argument at', i)
                return False
            if regex[i + 1] in ')|':
                print('ERROR | with missing argument at', i)
                return False
    return True

class RegexTree:

    @staticmethod
    def trim_brackets(regex):
        while regex[0] == '(' and regex[-1] == ')' and is_valid_regex(regex[1:-1]):
            regex = regex[1:-1]
        return regex
    
    @staticmethod
    def is_concat(c):
        return c == '(' or RegexTree.is_letter(c)
    
    @staticmethod
    def is_letter(c):
        return c == '#' or c.isalnum() or c in extended_symbols

    def __init__(self, regex):
        self.nullable = None
        self.firstpos = []
        self.lastpos = []
        self.item = None
        self.children = []

        if DEBUG:
            print('Current : '+regex)
        #Check if it is leaf
        if len(regex) == 1 and self.is_letter(regex):
            #Leaf
            self.item = regex
            #Lambda checking
            if use_lambda:
                if self.item == lambda_symbol:
                    self.nullable = True
                else:
                    self.nullable = False
            else:
                self.nullable = False
            return
        
        #It is an internal node
        #Finding the leftmost operators in all three
        kleene = -1
        or_operator = -1
        concatenation = -1
        i = 0

        #Getting the rest of terms    
        while i < len(regex):
            if regex[i] == '(':
                #Composed block
                bracketing_level = 1
                #Skipping the entire term
                i+=1
                while bracketing_level != 0 and i < len(regex):
                    if regex[i] == '(':
                        bracketing_level += 1
                    if regex[i] == ')':
                        bracketing_level -= 1
                    i+=1
            else:
                #Going to the next char
                i+=1
            
            #Found a concatenation in previous iteration
            #And also it was the last element check if breaking
            if i == len(regex):
                break

            #Testing if concatenation
            if self.is_concat(regex[i]):
                if concatenation == -1:
                    concatenation = i
                continue
            #Testing for kleene
            if regex[i] == '*':
                if kleene == -1:
                    kleene = i
                continue
            #Testing for or operator
            if regex[i] == '|':
                if or_operator == -1:
                    or_operator = i
        
        #Setting the current operation by priority
        if or_operator != -1:
            #Found an or operation
            self.item = '|'
            self.children.append(RegexTree(self.trim_brackets(regex[:or_operator])))
            self.children.append(RegexTree(self.trim_brackets(regex[(or_operator+1):])))
        elif concatenation != -1:
            #Found a concatenation
            self.item = '.'
            self.children.append(RegexTree(self.trim_brackets(regex[:concatenation])))
            self.children.append(RegexTree(self.trim_brackets(regex[concatenation:])))
        elif kleene != -1:
            #Found a kleene
            self.item = '*'
            self.children.append(RegexTree(self.trim_brackets(regex[:kleene])))
    
    def functions(self):
        self.calc_functions(1)

    def calc_functions(self, pos):
        if self.is_letter(self.item):
            #Is a leaf
            self.firstpos = [pos]
            self.lastpos = [pos]
            return pos+1
        #Is an internal node
        for child in self.children:
            pos = child.calc_functions(pos)
        #Calculate current functions

        if self.item == '.':
            #Is concatenation
            #Firstpos
            if self.children[0].nullable:
                self.firstpos = sorted(list(set(self.children[0].firstpos + self.children[1].firstpos)))
            else:
                self.firstpos = deepcopy(self.children[0].firstpos)
            #Lastpos
            if self.children[1].nullable:
                self.lastpos = sorted(list(set(self.children[0].lastpos + self.children[1].lastpos)))
            else:
                self.lastpos = deepcopy(self.children[1].lastpos)
            #Nullable
            self.nullable = self.children[0].nullable and self.children[1].nullable

        elif self.item == '|':
            #Is or operator
            #Firstpos
            self.firstpos = sorted(list(set(self.children[0].firstpos + self.children[1].firstpos)))
            #Lastpos
            self.lastpos = sorted(list(set(self.children[0].lastpos + self.children[1].lastpos)))
            #Nullable
            self.nullable = self.children[0].nullable or self.children[1].nullable

        elif self.item == '*':
            #Is kleene
            #Firstpos
            self.firstpos = deepcopy(self.children[0].firstpos)
            #Lastpos
            self.lastpos = deepcopy(self.children[0].lastpos)
            #Nullable
            self.nullable = True

        return pos

    def write(self):
        self.write_level(0)

    def write_level(self, level):
        print(str(level) + ' ' + self.item, self.firstpos, self.lastpos, self.nullable)
        for child in self.children:
            child.write_level(level+1)



#Preprocessing Functions
def preprocess(regex):
    regex = clean_kleene(regex)
    regex = regex.replace(' ','')
    regex = '(' + regex + ')' + '#'
    while '()' in regex:
        regex = regex.replace('()','')
    return regex

def clean_kleene(regex):
    for i in range(0, len(regex) - 1):
        while i < len(regex) - 1 and regex[i + 1] == regex[i] and regex[i] == '*':
            regex = regex[:i] + regex[i + 1:]
    return regex


#Settings
DEBUG = True
use_lambda = False
lambda_symbol = '_'
extended_symbols = lambda_symbol + '@%^'

#Main
regex = '(aa|b)*ab(bb|a)*'
regex = preprocess(regex)

#Check
if not is_valid_regex(regex):
    exit(0)

#Construct
tree = RegexTree(regex)
tree.functions()
tree.write()
