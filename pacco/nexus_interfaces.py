from typing import List, Tuple


class Client:
    """
    The client shall act like git as in only index files and not directory.
    """
    def if_file_exists(self, file_path: List[str]) -> bool:
        return True

    def get_file_content(self, file_path: List[str]) -> str:
        return 'hello world!'

    def write_file(self, content: str, file_path: List[str]) -> None:
        return

    def lsr_dir(self, dir_path: List[str]) -> List[Tuple[bool, str]]:
        return []

    def rm_dir(self, dir_path: List[str]) -> None:
        """
        rm_dir here means remove recursively all files within the directory
        """
        return

    def change_directory(self, dir_path: List[str]) -> None:
        return
