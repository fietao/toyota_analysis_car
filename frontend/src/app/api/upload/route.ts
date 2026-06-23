import { NextRequest, NextResponse } from "next/server";
import { promises as fs } from "fs";
import { execFile } from "child_process";
import { promisify } from "util";
import path from "path";

const execFileAsync = promisify(execFile);

let isRunning = false;

export async function POST(req: NextRequest) {
  if (isRunning) {
    return NextResponse.json(
      { error: "An update is already in progress. Please wait." },
      { status: 409 }
    );
  }
  isRunning = true;
  try {
    const formData = await req.formData();
    const fuelFile = formData.get("fuelFile") as File | null;
    const modelFile = formData.get("modelFile") as File | null;

    if (!fuelFile || !modelFile) {
      return NextResponse.json(
        { error: "Both fuelFile and modelFile are required." },
        { status: 400 }
      );
    }

    // Determine the tmp directory path (relative to this Next.js project)
    // frontend/src/app/api/upload/route.ts -> process.cwd() is 'frontend'
    const backendTmpDir = path.join(process.cwd(), "..", "backend", "tmp");

    // Ensure the tmp directory exists
    try {
      await fs.access(backendTmpDir);
    } catch {
      await fs.mkdir(backendTmpDir, { recursive: true });
    }

    // Sanitize filenames: strip directory components, enforce .xlsx/.xls, verify resolved path stays inside tmp
    const ALLOWED_EXT = /\.(xlsx|xls)$/i;
    function safeTmpPath(name: string): string {
      const base = path.basename(name);
      if (!ALLOWED_EXT.test(base)) throw new Error(`Invalid file type: ${base}`);
      const dest = path.join(backendTmpDir, base);
      if (!path.resolve(dest).startsWith(path.resolve(backendTmpDir) + path.sep)) {
        throw new Error("Invalid file path");
      }
      return dest;
    }

    // Save files
    const fuelFilePath = safeTmpPath(fuelFile.name);
    const modelFilePath = safeTmpPath(modelFile.name);

    const fuelBuffer = Buffer.from(await fuelFile.arrayBuffer());
    const modelBuffer = Buffer.from(await modelFile.arrayBuffer());

    await fs.writeFile(fuelFilePath, fuelBuffer);
    await fs.writeFile(modelFilePath, modelBuffer);

    // Execute the Python script
    // Python script is at `../backend/update_raw_data.py`
    const pythonScriptPath = path.join(process.cwd(), "..", "backend", "update_raw_data.py");
    
    // We run it with python. Assuming 'python' is in PATH.
    // Use execFile Async to avoid shell injection and safely pass Windows paths
    console.log("Running pipeline with execFile:", pythonScriptPath);
    const { stdout, stderr } = await execFileAsync("python", [pythonScriptPath, fuelFilePath, modelFilePath], { env: { ...process.env, PYTHONUTF8: "1" }, maxBuffer: 64 * 1024 * 1024 });
    
    console.log("Pipeline stdout:", stdout);
    if (stderr) {
      console.error("Pipeline stderr:", stderr);
    }

    // Delete the tmp files after successful run
    try {
      await fs.unlink(fuelFilePath);
      await fs.unlink(modelFilePath);
    } catch (cleanupError) {
      console.error("Failed to clean up tmp files:", cleanupError);
    }

    return NextResponse.json({ success: true, message: "Pipeline executed successfully" });

  } catch (error: any) {
    console.error("Upload API error:", error);
    return NextResponse.json(
      { error: "Failed to process upload and run pipeline.", details: error.message },
      { status: 500 }
    );
  } finally {
    isRunning = false;
  }
}
