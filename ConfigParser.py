from SingleSignalModel import SingleSignalModel


class ConfigParser:
    @staticmethod
    def load(filename) -> list[SingleSignalModel]:
        models: list[SingleSignalModel] = []
        with open(filename, "r") as f:
            config = (line.strip() for line in f.readlines())

        for line in config:
            try:
                (
                    fs,
                    hertz,
                    sigma,
                    duration,
                    start_offset,
                    stop_offset,
                    window,
                    window_open_length,
                    window_close_length,
                ) = line.split(",")
                models.append(
                    SingleSignalModel(
                        int(fs),
                        int(hertz),
                        float(sigma),
                        int(duration),
                        int(start_offset),
                        int(stop_offset),
                        window,
                        int(window_open_length),
                        int(window_close_length),
                    )
                )
            except ValueError as e:
                print(e)
                return []

        return models

    @staticmethod
    def save(filename: str, models: list[SingleSignalModel]):
        with open(filename, "w") as f:
            f.write("\n".join(str(m) for m in models))
