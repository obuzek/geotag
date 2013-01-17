from collections import namedtuple

Place = namedtuple("Place",["attributes",
                            "bounding_box",
                            "country",
                            "country_code",
                            "full_name",
                            "id",
                            "name",
                            "place_type",
                            "url"])
User = namedtuple("User",["id",
                          "name",
                          "screen_name",
                          "json"])
