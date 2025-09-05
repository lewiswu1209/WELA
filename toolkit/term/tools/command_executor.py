
from toolkit.term.tools.utils import sleep
from toolkit.term.tools.process_tracker import ProcessTracker
from toolkit.term.tools.tty_output_reader import TtyOutputReader

class CommandExecutor:

    def __init__(self, shell):
        """
        :param shell: The pexpect.spawn object representing our shell session
        """
        self.shell = shell

    async def execute_command(self, command: str, continuous_check_threshold: int = 100) -> str:
        """
        Execute the given 'command' in our shell session.
        1) Read leftover output first
        2) Send command
        3) Wait until shell is 'idle' (连续多次检测CPU使用率<1%或无活跃进程)
        4) Return entire buffer or new lines
        
        :param command: 待执行的命令
        :param continuous_check_threshold: 连续空闲检测阈值（默认3次），可根据需求调整
        """
        # 1. 先读取残留输出，避免与本次命令输出混淆
        TtyOutputReader.read_shell_output(self.shell)

        # 2. 发送命令到Shell
        self.shell.sendline(command)

        # 短延迟确保输出开始产生（避免刚发命令就检测导致漏读）
        await sleep(0.2)

        # 3. 基于CPU监控等待空闲（添加连续检测逻辑）
        tracker = ProcessTracker()
        continuous_idle_count = 0  # 连续空闲计数器：记录连续多少次检测到空闲状态

        while True:
            # 每次循环先读取新产生的输出，避免输出堆积
            TtyOutputReader.read_shell_output(self.shell)

            # 获取当前活跃进程
            active_process = tracker.get_active_process()
            # 判断当前是否为空闲状态（无活跃进程 或 CPU使用率<1%）
            is_idle = not active_process or active_process["metrics"]["totalCPUPercent"] < 1

            if is_idle:
                # 空闲状态：计数器+1
                continuous_idle_count += 1
                # 若连续空闲次数达到阈值，判定任务完成
                if continuous_idle_count >= continuous_check_threshold:
                    # 额外等待0.2秒，确保最后一批输出被捕获
                    print(continuous_idle_count)
                    await sleep(0.2)
                    TtyOutputReader.read_shell_output(self.shell)
                    break
            else:
                # 非空闲状态：重置计数器（打破连续记录）
                continuous_idle_count = 0

            # 每次检测间隔0.1秒（平衡响应速度与CPU占用）
            await sleep(0.2)

        # 4. 最终读取一次输出，确保完整性
        TtyOutputReader.read_shell_output(self.shell)
        after_buffer = TtyOutputReader.get_buffer()

        return after_buffer
