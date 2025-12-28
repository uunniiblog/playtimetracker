class SystemUtils:
    @staticmethod
    def is_wine_or_proton(utils, pid):
        if not utils: return False
        try:
            env_result = utils.get_process_environ(pid)
            # print(f'env_result: {env_result}')          
            return ".exe" in env_result
        except Exception as e:
            print(f"[ERROR] is_wine_or_proton failed: {e}")
            return False

    @staticmethod
    def get_window_list(utils, only_show_wine=False):
        """Returns a list of tuples: (title, window_id) using the detected DE utils."""
        if not utils: return []

        window_list = []
        try:
            window_ids = utils.get_all_window_ids()

            for wid in window_ids:
                try:
                    title = utils.get_window_name(wid)
                    if not title:
                        continue

                    if only_show_wine:
                        pid_str = utils.get_window_pid(wid)
                        if pid_str and pid_str.isdigit() and SystemUtils.is_wine_or_proton(utils, int(pid_str)):
                            window_list.append((title, wid))
                    else:
                        window_list.append((title, wid))
                except Exception:
                    continue
        except Exception:
            pass

        return window_list
