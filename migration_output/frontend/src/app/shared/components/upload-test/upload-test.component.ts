import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { DataService } from '../../../core/services/data.service';

@Component({
  selector: 'app-upload-test',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './upload-test.component.html',
  styleUrl: './upload-test.component.scss'
})
export class UploadTestComponent {
  dataService = inject(DataService);
  isDragging = false;

  onDragOver(event: DragEvent) {
    event.preventDefault();
    this.isDragging = true;
  }

  onDragLeave(event: DragEvent) {
    event.preventDefault();
    this.isDragging = false;
  }

  onDrop(event: DragEvent) {
    event.preventDefault();
    this.isDragging = false;
    
    if (event.dataTransfer?.files && event.dataTransfer.files.length > 0) {
      const file = event.dataTransfer.files[0];
      this.handleFile(file);
    }
  }

  onFileSelected(event: any) {
    if (event.target.files && event.target.files.length > 0) {
      const file = event.target.files[0];
      this.handleFile(file);
    }
  }

  handleFile(file: File) {
    const validExtensions = ['.xlsx', '.xls', '.csv'];
    const fileExtension = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
    
    if (!validExtensions.includes(fileExtension)) {
      alert('Invalid file format. Please upload an Excel or CSV file (.xlsx, .xls, .csv)');
      return;
    }
    
    this.dataService.uploadFile(file);
  }

  toggleMockMode() {
    this.dataService.isMockMode.set(!this.dataService.isMockMode());
  }
}
