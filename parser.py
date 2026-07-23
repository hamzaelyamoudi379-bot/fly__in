from typing import Optional
from zone import Zone
from connection import Connection

VALID_ZONE_TYPES = {"normal", "blocked", "restricted", "priority"}


class Parser:
    """Reads and parses a map configuration file describing zones,
    connections, start/end hubs and the number of drones.

    After calling read_file(), the parsed data is available on
    self.zone, self.connections, self.start, self.end and
    self.nb_drons.
    """

    def __init__(self, file_name: str) -> None:
        """Initialize the parser with the path to the map file to read.
        No parsing happens until read_file() is called.
        """
        self.file_name = file_name
        self.zone: dict[str, Zone] = {}
        self.connections: list[Connection] = []
        self.start: Optional[Zone] = None
        self.end: Optional[Zone] = None
        self.nb_drons = 0

    def read_file(self) -> None:
        """Read and parse the map file line by line, populating
        self.zone, self.connections, self.start, self.end and
        self.nb_drons.

        Raises ValueError if the file contains invalid syntax,
        duplicate zones/connections, missing start_hub/end_hub, or an
        invalid nb_drones value.
        """
        connection_set: set[tuple[str, str]] = set()
        find = True

        with open(self.file_name, "r") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()

                if not line or line.startswith("#"):
                    continue

                try:
                    if find:
                        if not line.startswith("nb_drones:"):
                            raise ValueError(f"The nb drons not find ")
                        find = False
                    if line.startswith("nb_drones:"):
                        self._parse_nb_drones(line, line_num)

                    elif line.startswith("start_hub:"):
                        if self.start is not None:
                            raise ValueError(
                                f"Line {line_num}: multiple start_hub defined"
                            )
                        self.start = self._parse_zone(line, "start_hub")
                        self.zone[self.start.name] = self.start

                    elif line.startswith("end_hub:"):
                        if self.end is not None:
                            raise ValueError(
                                f"Line {line_num}: multiple end_hub defined"
                            )
                        self.end = self._parse_zone(line, "end_hub")
                        self.zone[self.end.name] = self.end

                    elif line.startswith("hub:"):
                        new = self._parse_zone(line, "hub")
                        if new.name in self.zone:
                            raise ValueError(
                                f"Line {line_num}: " f"duplicate zone name \
'{new.name}'"
                            )
                        self.zone[new.name] = new

                    elif line.startswith("connection:"):
                        conn = self._parse_connection(line, line_num)
                        pair = (
                            (conn.zone1, conn.zone2)
                            if conn.zone1 < conn.zone2
                            else (conn.zone2, conn.zone1)
                        )
                        if pair in connection_set:
                            raise ValueError(
                                f"Line {line_num}: "
                                f"duplicate connection '{conn.zone1}"
                                f"-{conn.zone2}'"
                            )
                        connection_set.add(pair)
                        self.connections.append(conn)

                    else:
                        raise ValueError(f"Line {line_num}:\
unknown line format")

                except ValueError:
                    raise

        if self.start is None:
            raise ValueError("Error: 'start_hub' is missing in the file")
        if self.end is None:
            raise ValueError("Error: 'end_hub' is missing in the file")
        if self.nb_drons <= 0:
            raise ValueError("Error: nb_drones must be greater than 0")

    def _parse_nb_drones(self, line: str, line_num: int) -> None:
        """Parse an 'nb_drones:' line and set self.nb_drons.

        Raises ValueError if the value is not a positive integer.
        """
        value = line.split(":", 1)[1].strip()
        try:
            self.nb_drons = int(value)
        except ValueError:
            raise ValueError(f"Line {line_num}: nb_drones must \
be a positive integer")
        if self.nb_drons <= 0:
            raise ValueError(f"Line {line_num}: nb_drones must \
be greater than 0")

    def _parse_metadata(self, raw: str) -> dict[str, str]:
        """Parse a bracketed metadata string (e.g. '[color=red
        max_drones=2]') into a dict of key/value pairs.

        Raises ValueError if a key appears more than once.
        """
        meta: dict[str, str] = {}
        # print(raw)
        if "[" not in raw or "]" not in raw:
            raise ValueError(f"The '{raw}' most has a format of [metat data] >>[]")
        raw = raw.strip("[] ")
        # print(raw)

        for token in raw.split():
            # print(token)
            if "=" not in token:
                raise ValueError(f"it most has a '=' on it ")
            if "=" not in token:
                continue

            key, val = token.split("=", 1)
            key = key.strip()
            val = val.strip()

            if key in meta:
                raise ValueError(f"Duplicate metadata key '{key}'")

            meta[key] = val

        return meta

    def _parse_zone(self, line: str, prefix: str) -> Zone:
        """Parse a hub/start_hub/end_hub line into a Zone object.

        Expects the format 'name x y [metadata]', where metadata may
        include zone, color and max_drones. Raises ValueError on any
        malformed field (missing parts, non-integer coordinates,
        invalid zone type, invalid name, or invalid max_drones).
        """
        color: Optional[str] = None
        max_drones = 1
        zone_type = "normal"

        value = line.split(":", 1)[1].strip()
        parts = value.split()

        if len(parts[1:]) < 3:
            raise ValueError(f"Invalid {prefix} line: \
expected name x y [metadata]")

        name = parts[0]
        # print((parts[3]))
        if "-" in name or " " in name:
            raise ValueError(f"Zone name '{name}' must \
not contain dashes or spaces")

        try:
            x = int(parts[1])
            y = int(parts[2])
            # print(parts)
            # print(len(parts))

        except ValueError:
            raise ValueError(f"Zone '{name}': coordinates must be integers")

        if not parts[3].startswith("["):
            raise ValueError(
                f"Zone '{name}': expected only two coordinates (x y), "
                f"found extra value '{parts[3]}'"
            )

        if len(parts) > 3:
            meta_str = " ".join(parts[3:])
            meta = self._parse_metadata(meta_str)

            # print(meta)
            if "zone" in meta:
                zone_type = meta["zone"]
                if zone_type not in VALID_ZONE_TYPES:
                    raise ValueError(
                        f"Zone '{name}': invalid zone type '{zone_type}'. "
                        f"Must be one of {VALID_ZONE_TYPES}"
                    )
            allowed_keys = {"color", "max_drones", "zone"}

            invalid_keys = set(meta) - allowed_keys

            if invalid_keys:
                raise ValueError(f"Invalid metadata keys: {', '.join(sorted(invalid_keys))}")

            if "color" in meta:
                color = meta["color"]
            if "max_drones" in meta:

                try:
                    max_drones = int(meta["max_drones"])
                    if max_drones <= 0:
                        raise ValueError()

                except ValueError:
                    raise ValueError(f"Zone '{name}': max_drones \
must be " f"a positive integer")

        return Zone(name, x, y, color, max_drones, zone_type)

    def _parse_connection(self, line: str, line_num: int) -> Connection:
        """Parse a 'connection:' line into a Connection object.

        Expects the format 'zone1-zone2 [metadata]', where metadata
        may include max_link_capacity. Raises ValueError if the format
        is invalid, either zone is undefined, a zone connects to
        itself, or max_link_capacity is not a positive integer.
        """
        max_link_capacity = 1
        value = line.split(":", 1)[1].strip()

        meta_str = ""
        if "[" in value:
            bracket_start = value.index("[")
            meta_str = value[bracket_start:]
            value = value[:bracket_start].strip()

        if "-" not in value:
            raise ValueError(f"Line {line_num}: \
connection must use format zone1-zone2")

        parts = value.split("-")
        if len(parts) != 2:
            raise ValueError(
                f"Line {line_num}: connection must have exactly two zone names"
            )

        zone1 = parts[0].strip()
        zone2 = parts[1].strip()

        if zone1 == zone2:
            raise ValueError(f"Line {line_num}: a zone cannot \
connect to itself")
        if zone1 not in self.zone:
            raise ValueError(f"Line {line_num}: undefined zone '{zone1}'")
        if zone2 not in self.zone:
            raise ValueError(f"Line {line_num}: undefined zone '{zone2}'")

        # print(meta_str)
        if meta_str:
            meta = self._parse_metadata(meta_str)
            allowed_keys = {"max_link_capacity"}

            invalid_keys = set(meta) - allowed_keys
            if "max_link_capacity" not in meta or len(meta) != 1:
                raise ValueError(f"Ivalide metadata {invalid_keys}")
            # print (meta)
            if "max_link_capacity" in meta:
                try:
                    max_link_capacity = int(meta["max_link_capacity"])
                    if max_link_capacity <= 0:
                        raise ValueError()
                except ValueError:
                    raise ValueError(
                        f"Line {line_num}: max_link_capacity must be "
                        f"a positive integer"
                    )

        return Connection(zone1, zone2, max_link_capacity)
