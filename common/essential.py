import sys
import dotenv

class essentials:
    def __init__(self, loop=None):
        self.loop = loop
        self.get_essentials()
        self.do_essentials()

    def get_essentials(self):
        self.sys = sys
        try:
            if self.loop != None:
                import nest_asyncio
                self.nest_asyncio = nest_asyncio
            self.dotenv = dotenv
        except ImportError:
            print("Failed to import dependencies : essentials")
            sys.exit(1)

    def do_essentials(self):
        try:
            self.dotenv.load_dotenv()
            if self.loop != None:
                self.nest_asyncio.apply(self.loop)
        except Exception as e:
            print(e)
            print("Failed to do essentials")
            self.sys.exit(1)
