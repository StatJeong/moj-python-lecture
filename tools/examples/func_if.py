def 연령대(나이):
    if 나이 < 30:
        return "30세 미만"
    elif 나이 < 40:
        return "30대"
    return "40세 이상"

for 나이 in [24, 45]:
    print(나이, 연령대(나이))
