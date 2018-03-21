from corpus import all_questions
from corpus.responsetemplates import all_response_templates


def main():
    print("The following strings might be generated:\n")
    print("=== Question surroundings ===")
    question_surroundings = all_response_templates['question_surrounding']
    for q in all_questions:
        for s in question_surroundings:
            text = s.text_template.render({'question': q})
            print(text)

    print()
    print("=== Hint surroundings ===")
    hint_surroundings = all_response_templates['hint_surrounding']
    for q in all_questions:
        for s in hint_surroundings:
            text = s.text_template.render({'question': q})
            print(text)


if __name__ == '__main__':
    main()
