flowchart LR
    subgraph PC
        A(Windows Task Scheduler)
    end

    subgraph Telegram
        B(Telegram Bot)
    end

    subgraph EC2_Ubuntu
        C1(Cron Job)
        C2("Cleanup\n(Delete local files)")
    end

    subgraph AWS["AWS Cloud"]
        S3((AWS S3 Bucket))
    end

    A -->|SCP w/ SSH Key| EC2_Ubuntu
    B -->|File Upload\n'killswitch' Command| EC2_Ubuntu

    EC2_Ubuntu -->|Detect New Files| C1
    C1 -->|aws s3 cp| S3
    C1 -->|Post-upload| C2

    B -->|Telegram Status\nNotifications| B
