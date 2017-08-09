import tornado.ioloop
import tornado.web
import os


class MainHandler(tornado.web.RequestHandler):

    def get(self):
        self.write("Hello, world.")


def bootstrap_app():
    return tornado.web.Application(
        [
            (r"/", MainHandler),
        ],
        template_path=os.path.join(os.path.dirname(__file__), "templates"),
    )


def main():
    app = bootstrap_app()
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()

if __name__ == '__main__':
    main()
