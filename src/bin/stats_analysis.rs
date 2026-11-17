use std::collections::BTreeMap;
use std::fs::File;
use std::io::{BufRead, BufReader, Write};

#[derive(Debug, Clone)]
#[allow(dead_code)]
struct RawRecord {
    imp: String,
    size: usize,
    distribution: String,
    operation: String,
    trial: usize,
    time_ns: f64,
    collisions: usize,
    avg_probe: f64,
    max_probe: usize,
    load_factor: f64,
    memory_bytes: usize,
}

#[derive(Debug, PartialEq, Eq, PartialOrd, Ord)]
struct GroupKey {
    imp: String,
    size: usize,
    distribution: String,
    operation: String,
}

fn median_f64(mut vals: Vec<f64>) -> f64 {
    vals.sort_by(|a, b| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal));
    let n = vals.len();
    if n == 0 {
        return 0.0;
    }
    if n % 2 == 1 {
        vals[n / 2]
    } else {
        (vals[n / 2 - 1] + vals[n / 2]) / 2.0
    }
}

fn iqr_f64(mut vals: Vec<f64>) -> f64 {
    vals.sort_by(|a, b| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal));
    let n = vals.len();
    if n < 4 {
        return vals.last().unwrap_or(&0.0) - vals.first().unwrap_or(&0.0);
    }
    // Standard quartile calculation:
    // For n=7: lower half is [0, 1, 2] -> median is index 1
    //          upper half is [4, 5, 6] -> median is index 5
    let lower_half = &vals[0..n / 2];
    let upper_half = if n % 2 == 1 {
        &vals[(n / 2 + 1)..n]
    } else {
        &vals[(n / 2)..n]
    };
    let q1 = median_f64(lower_half.to_vec());
    let q3 = median_f64(upper_half.to_vec());
    (q3 - q1).max(0.0)
}

fn main() {
    println!("============================================================");
    println!(" Hash Table Statistical Analysis Runner");
    println!("============================================================");

    let input_path = "results/raw_experiments.csv";
    let output_path = "results/summary_stats.csv";

    let file = File::open(input_path).unwrap_or_else(|e| {
        panic!("Failed to open {}: {}", input_path, e);
    });
    let reader = BufReader::new(file);

    let mut groups: BTreeMap<GroupKey, Vec<RawRecord>> = BTreeMap::new();
    let mut header_skipped = false;

    for (line_no, line) in reader.lines().enumerate() {
        let line = line.expect("Failed to read line");
        let line = line.trim();
        if line.is_empty() {
            continue;
        }
        if !header_skipped {
            header_skipped = true;
            continue;
        }

        let parts: Vec<&str> = line.split(',').collect();
        if parts.len() < 11 {
            eprintln!("Warning: Skipping malformed line {}: {}", line_no, line);
            continue;
        }

        let record = RawRecord {
            imp: parts[0].to_string(),
            size: parts[1].parse().expect("Invalid size"),
            distribution: parts[2].to_string(),
            operation: parts[3].to_string(),
            trial: parts[4].parse().expect("Invalid trial"),
            time_ns: parts[5].parse().expect("Invalid time_ns"),
            collisions: parts[6].parse().expect("Invalid collisions"),
            avg_probe: parts[7].parse().expect("Invalid avg_probe"),
            max_probe: parts[8].parse().expect("Invalid max_probe"),
            load_factor: parts[9].parse().expect("Invalid load_factor"),
            memory_bytes: parts[10].parse().expect("Invalid memory_bytes"),
        };

        let key = GroupKey {
            imp: record.imp.clone(),
            size: record.size,
            distribution: record.distribution.clone(),
            operation: record.operation.clone(),
        };

        groups.entry(key).or_default().push(record);
    }

    println!("Read {} distinct benchmark groups from {}", groups.len(), input_path);

    let mut out_file = File::create(output_path).unwrap_or_else(|e| {
        panic!("Failed to create {}: {}", output_path, e);
    });

    // CSV Header as requested:
    // impl,size,distribution,operation,median_ns,iqr_ns,mean_ns,min_ns,max_ns,collisions,avg_probe,max_probe,load_factor,memory_bytes
    writeln!(
        out_file,
        "impl,size,distribution,operation,median_ns,iqr_ns,mean_ns,min_ns,max_ns,collisions,avg_probe,max_probe,load_factor,memory_bytes"
    )
    .expect("Failed to write CSV header");

    let mut rows_written = 0;
    for (key, records) in &groups {
        let mut times: Vec<f64> = records.iter().map(|r| r.time_ns).collect();
        times.sort_by(|a, b| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal));

        let min_ns = times.first().copied().unwrap_or(0.0);
        let max_ns = times.last().copied().unwrap_or(0.0);
        let median_ns = median_f64(times.clone());
        let iqr_ns = iqr_f64(times.clone());
        let mean_ns = times.iter().sum::<f64>() / times.len() as f64;

        let collisions = records.iter().map(|r| r.collisions).max().unwrap_or(0);
        let avg_probe = median_f64(records.iter().map(|r| r.avg_probe).collect());
        let max_probe = records.iter().map(|r| r.max_probe).max().unwrap_or(0);
        let load_factor = median_f64(records.iter().map(|r| r.load_factor).collect());
        let memory_bytes = records.iter().map(|r| r.memory_bytes).max().unwrap_or(0);

        writeln!(
            out_file,
            "{},{},{},{},{:.2},{:.2},{:.2},{:.2},{:.2},{},{:.4},{},{:.4},{}",
            key.imp,
            key.size,
            key.distribution,
            key.operation,
            median_ns,
            iqr_ns,
            mean_ns,
            min_ns,
            max_ns,
            collisions,
            avg_probe,
            max_probe,
            load_factor,
            memory_bytes
        )
        .expect("Failed to write summary row");
        rows_written += 1;
    }

    out_file.flush().unwrap();
    println!("Successfully computed summary statistics!");
    println!("Written {} summary rows to {}", rows_written, output_path);
    println!("============================================================");
}
