class GermanPronoun:
    class Kind:
        POSSESSIVE = 'possessive'
        PERSONAL = 'personal'

    class Case:
        GENITIVE = 'genitive'
        DATIVE = 'dative'
        NOMINATIVE = 'nominative'
        ACCUSATIVE = 'accusative'

    class Gender:
        ANY = 'any'
        MASCULINE = 'masculine'
        FEMININE = 'feminine'
        NEUTER = 'neuter'
        PLURAL = 'plural'

    @staticmethod
    def pronoun(formal: bool, kind: Kind, case: Case, gender: Gender):
        """
        Personal and possessive pronouns in german language, 2nd person (you)
        """
        if kind == GermanPronoun.Kind.POSSESSIVE:
            if gender is None or gender == GermanPronoun.Gender.ANY:
                raise ValueError("Possessive pronoun without gender is invalid grammar.")

            result = 'Ihr' if formal else 'dein'

            if gender == GermanPronoun.Gender.MASCULINE:
                if case == GermanPronoun.Case.NOMINATIVE:
                    return result
                elif case == GermanPronoun.Case.GENITIVE:
                    return result + 'es'
                elif case == GermanPronoun.Case.DATIVE:
                    return result + 'em'
                elif case == GermanPronoun.Case.ACCUSATIVE:
                    return result + 'en'
            elif gender == GermanPronoun.Gender.FEMININE:
                if case == GermanPronoun.Case.NOMINATIVE:
                    return result + 'e'
                elif case == GermanPronoun.Case.GENITIVE:
                    return result + 'er'
                elif case == GermanPronoun.Case.DATIVE:
                    return result + 'er'
                elif case == GermanPronoun.Case.ACCUSATIVE:
                    return result + 'e'
            elif gender == GermanPronoun.Gender.NEUTER:
                if case == GermanPronoun.Case.NOMINATIVE:
                    return result
                elif case == GermanPronoun.Case.GENITIVE:
                    return result + 'es'
                elif case == GermanPronoun.Case.DATIVE:
                    return result + 'em'
                elif case == GermanPronoun.Case.ACCUSATIVE:
                    return result
            elif gender == GermanPronoun.Gender.PLURAL:
                if case == GermanPronoun.Case.NOMINATIVE:
                    return result + 'e'
                elif case == GermanPronoun.Case.GENITIVE:
                    return result + 'er'
                elif case == GermanPronoun.Case.DATIVE:
                    return result + 'en'
                elif case == GermanPronoun.Case.ACCUSATIVE:
                    return result + 'e'

        elif kind == GermanPronoun.Kind.PERSONAL:
            if case == GermanPronoun.Case.NOMINATIVE:
                return 'Sie' if formal else 'du'
            elif case == GermanPronoun.Case.GENITIVE:
                return 'Ihrer' if formal else 'deiner'
            elif case == GermanPronoun.Case.DATIVE:
                return 'Ihnen' if formal else 'dir'
            elif case == GermanPronoun.Case.ACCUSATIVE:
                return 'sich' if formal else 'dich'


if __name__ == '__main__':
    def print_it(args):
        print('formal' if args[0] else 'informal', *args[1:], ": ", GermanPronoun.pronoun(*args))

    args = (True, 'possessive', 'dative', 'masculine')
    print_it(args)
    args = (False, 'possessive', 'dative', 'masculine')
    print_it(args)
    args = (False, 'possessive', 'accusative', 'feminine')
    print_it(args)
    args = (False, 'possessive', 'genitive', 'masculine')
    print_it(args)
    args = (True, 'personal', 'accusative', None)
    print_it(args)
