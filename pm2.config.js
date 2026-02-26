/**
 * PM2 Ecosystem Config — AI Employee
 *
 * Start all processes:   pm2 start pm2.config.js
 * Stop all:              pm2 stop all
 * Restart all:           pm2 restart all
 * View logs:             pm2 logs
 * Monitor live:          pm2 monit
 * Save + auto-boot:      pm2 save && pm2 startup
 */

module.exports = {
  apps: [
    {
      name: "ai-employee-scheduler",
      script: "sentinels/scheduler.py",
      interpreter: "python",
      cwd: "C:/Users/Amena/Desktop/ai-empolyee",
      autorestart: true,
      watch: false,
      max_restarts: 10,
      restart_delay: 5000,
      log_file: "logs/scheduler.log",
      merge_logs: true,
      env: {
        DRY_RUN: "false",
        PYTHONUNBUFFERED: "1",
      },
    },
  ],
};
