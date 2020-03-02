class People():
    def __init__(self, name, gender):
        self.name = name
        self.gender = gender

    @staticmethod
    def greeting(name, gender):
        return f'Hello, {name}!'


print(People.greeting('Anders', 'Male'))

# 输出内容：
# Hello, Anders!
People.greeting("name")