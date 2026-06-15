import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { DataService } from '../../core/services/data.service';

@Component({
  selector: 'app-landing',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './landing.component.html',
  styleUrl: './landing.component.scss'
})
export class LandingComponent {
  dataService = inject(DataService);
  private router = inject(Router);

  onFileSelected(event: any) {
    const file = event.target.files[0];
    if (file) {
      this.dataService.uploadFile(file);
    }
  }

  onPartySelected(event: any) {
    const file = event.target.files[0];
    if (file) {
      this.dataService.uploadPartyMaster(file);
    }
  }

  onOfacSelected(event: any) {
    const file = event.target.files[0];
    if (file) {
      this.dataService.uploadOfac(file);
    }
  }

  goToHome() {
    this.router.navigate(['/home']);
  }
}
